"""Create a synthetic Spring MVC + MyBatis project for AI Commit Advisor demos."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

try:
    from scripts.generate_sample_development_data import generate_sample_data, write_excel
except ModuleNotFoundError:
    from generate_sample_development_data import generate_sample_data, write_excel


KST = timezone(timedelta(hours=9))
BASE_PACKAGE_PATH = "src/main/java/com/example/market"
RESOURCE_MAPPER_PATH = "src/main/resources/mappers"
WEBAPP_PATH = "src/main/webapp/WEB-INF/views"


@dataclass(frozen=True)
class Developer:
    name: str
    email: str
    role: str
    skills: str


@dataclass(frozen=True)
class CommitStep:
    message: str
    author: Developer
    days_after_start: int
    files: dict[str, str]


DEVELOPERS = {
    "pm": Developer("최현우", "hyunwoo.choi@sample.local", "PM", "사업관리, 일정관리, 고객 협의"),
    "pl": Developer("오세훈", "sehun.oh@sample.local", "PL", "요구사항 분석, 설계 검토, 개발 리딩"),
    "order": Developer("김민수", "minsu.kim@sample.local", "개발자", "주문 업무, Spring MVC, JSP, MyBatis"),
    "inventory": Developer("박지훈", "jihoon.park@sample.local", "개발자", "재고/매출 업무, Spring MVC, JSP, MyBatis"),
    "payment": Developer("이지은", "jieun.lee@sample.local", "개발자", "결제/대시보드 업무, Spring MVC, JSP, MyBatis"),
    "qa": Developer("정서연", "seoyeon.jung@sample.local", "QA", "테스트 케이스, 결함 관리, 검수 지원"),
}


PROGRAM_ROWS = [
    {
        "프로그램ID": "SMP-ORD-001",
        "프로그램명": "주문 접수",
        "주요기능": "orders",
        "주요URL/화면": "/orders/new",
        "기능설명": "고객 주문을 생성하고 장바구니 품목을 주문 라인으로 확정합니다.",
        "Controller": "OrderController.java",
        "Service": "OrderService.java",
        "Mapper/Repository": "OrderMapper.java, OrderMapper.xml",
    },
    {
        "프로그램ID": "SMP-ORD-002",
        "프로그램명": "주문 상태 변경",
        "주요기능": "orders",
        "주요URL/화면": "/orders/{orderId}/status",
        "기능설명": "결제대기, 준비중, 배송중, 완료 상태 전환과 변경 이력을 관리합니다.",
        "Controller": "OrderController.java",
        "Service": "OrderStatusService.java",
        "Mapper/Repository": "OrderMapper.java, OrderMapper.xml",
    },
    {
        "프로그램ID": "SMP-INV-001",
        "프로그램명": "재고 예약",
        "주요기능": "inventory",
        "주요URL/화면": "/inventory/reservations",
        "기능설명": "주문 생성 시 판매 가능 수량을 확인하고 재고를 예약합니다.",
        "Controller": "InventoryController.java",
        "Service": "InventoryService.java",
        "Mapper/Repository": "InventoryMapper.java, InventoryMapper.xml",
    },
    {
        "프로그램ID": "SMP-PAY-001",
        "프로그램명": "결제 승인",
        "주요기능": "payments",
        "주요URL/화면": "/payments/authorize",
        "기능설명": "결제 요청을 검증하고 승인 결과를 주문 상태에 반영합니다.",
        "Controller": "PaymentController.java",
        "Service": "PaymentService.java",
        "Mapper/Repository": "PaymentMapper.java, PaymentMapper.xml",
    },
    {
        "프로그램ID": "SMP-RPT-001",
        "프로그램명": "매출 현황",
        "주요기능": "reports",
        "주요URL/화면": "/reports/sales",
        "기능설명": "일자별 주문 금액, 결제 상태, 취소 금액을 집계합니다.",
        "Controller": "ReportController.java",
        "Service": "SalesReportService.java",
        "Mapper/Repository": "ReportMapper.java, ReportMapper.xml",
    },
    {
        "프로그램ID": "SMP-UI-001",
        "프로그램명": "운영 대시보드",
        "주요기능": "dashboard",
        "주요URL/화면": "/dashboard",
        "기능설명": "주문, 재고, 결제, 리스크 상태를 운영자가 한 화면에서 확인합니다.",
        "Controller": "DashboardController.java",
        "Service": "DashboardService.java",
        "Mapper/Repository": "DashboardMapper.java, DashboardMapper.xml",
    },
]


def _repo_default_path() -> Path:
    return Path(__file__).resolve().parents[2] / "ai-advisor-sample-shop"


def _run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True, env=env)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def _remove_readonly(func, path: str, _exc_info) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _commit(repo_path: Path, step: CommitStep, start_at: datetime) -> None:
    for relative_path, content in step.files.items():
        _write(repo_path / relative_path, content)

    _run(["git", "add", "."], cwd=repo_path)
    committed_at = start_at + timedelta(days=step.days_after_start)
    date_value = committed_at.isoformat()
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": step.author.name,
            "GIT_AUTHOR_EMAIL": step.author.email,
            "GIT_AUTHOR_DATE": date_value,
            "GIT_COMMITTER_NAME": step.author.name,
            "GIT_COMMITTER_EMAIL": step.author.email,
            "GIT_COMMITTER_DATE": date_value,
        }
    )
    _run(["git", "commit", "-m", step.message], cwd=repo_path, env=env)


def _program_csv(repo_path: Path) -> None:
    pd.DataFrame(PROGRAM_ROWS).to_csv(repo_path / "샘플_프로그램목록.csv", index=False, encoding="utf-8-sig")


def _apply_developer_profiles(developers: pd.DataFrame) -> pd.DataFrame:
    by_email = {developer.email: developer for developer in DEVELOPERS.values()}
    result = developers.copy()
    for index, row in result.iterrows():
        profile = by_email.get(str(row.get("email") or ""))
        if profile is None:
            continue
        result.at[index, "role"] = profile.role
        result.at[index, "skills"] = profile.skills
    return result


def _commit_steps() -> list[CommitStep]:
    return [
        CommitStep(
            "Initialize Spring MyBatis market operations project",
            DEVELOPERS["pm"],
            0,
            {
                "README.md": """
                # AI Advisor Sample Shop

                Synthetic Spring MVC + MyBatis retail operations project for AI Commit Advisor demos.
                Every file and commit is fake, so it is safe to index, map, and review.
                """,
                "pom.xml": """
                <project xmlns="http://maven.apache.org/POM/4.0.0"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
                    <modelVersion>4.0.0</modelVersion>
                    <groupId>com.example</groupId>
                    <artifactId>ai-advisor-sample-shop</artifactId>
                    <version>0.1.0</version>
                    <packaging>war</packaging>
                    <properties>
                        <java.version>17</java.version>
                        <spring.version>5.3.39</spring.version>
                    </properties>
                    <dependencies>
                        <dependency>
                            <groupId>org.springframework</groupId>
                            <artifactId>spring-webmvc</artifactId>
                            <version>${spring.version}</version>
                        </dependency>
                        <dependency>
                            <groupId>org.mybatis</groupId>
                            <artifactId>mybatis</artifactId>
                            <version>3.5.16</version>
                        </dependency>
                    </dependencies>
                </project>
                """,
                f"{BASE_PACKAGE_PATH}/config/WebMvcConfig.java": """
                package com.example.market.config;

                import org.springframework.context.annotation.Configuration;
                import org.springframework.web.servlet.config.annotation.EnableWebMvc;
                import org.springframework.web.servlet.config.annotation.ViewResolverRegistry;
                import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

                @Configuration
                @EnableWebMvc
                public class WebMvcConfig implements WebMvcConfigurer {
                    @Override
                    public void configureViewResolvers(ViewResolverRegistry registry) {
                        registry.jsp("/WEB-INF/views/", ".jsp");
                    }
                }
                """,
                "src/main/resources/mybatis-config.xml": """
                <?xml version="1.0" encoding="UTF-8" ?>
                <!DOCTYPE configuration PUBLIC "-//mybatis.org//DTD Config 3.0//EN"
                  "https://mybatis.org/dtd/mybatis-3-config.dtd">
                <configuration>
                    <settings>
                        <setting name="mapUnderscoreToCamelCase" value="true"/>
                    </settings>
                </configuration>
                """,
            },
        ),
        CommitStep(
            "Review program list and development plan baseline",
            DEVELOPERS["pl"],
            1,
            {
                "docs/requirements/program-baseline.md": """
                # 프로그램 기준선

                - 주문 접수와 주문 상태 변경은 1차 오픈 범위로 본다.
                - 재고 예약은 주문 접수 전후 정합성을 확인한다.
                - 결제 승인 후 주문 상태가 PAID로 전환되어야 한다.
                - 매출 현황과 운영 대시보드는 조회 성능을 별도 점검한다.
                """,
                "docs/requirements/interface-policy.md": """
                # 인터페이스 정책

                - Controller는 화면/요청 단위 진입점만 담당한다.
                - Service는 트랜잭션과 업무 규칙을 담당한다.
                - Mapper XML은 SQL과 result mapping을 담당한다.
                """,
            },
        ),
        CommitStep(
            "Add order creation controller service and mapper",
            DEVELOPERS["order"],
            2,
            {
                f"{BASE_PACKAGE_PATH}/order/controller/OrderController.java": """
                package com.example.market.order.controller;

                import com.example.market.order.service.OrderService;
                import org.springframework.stereotype.Controller;
                import org.springframework.ui.Model;
                import org.springframework.web.bind.annotation.GetMapping;
                import org.springframework.web.bind.annotation.PostMapping;
                import org.springframework.web.bind.annotation.RequestMapping;
                import org.springframework.web.bind.annotation.RequestParam;

                @Controller
                @RequestMapping("/orders")
                public class OrderController {
                    private final OrderService orderService;

                    public OrderController(OrderService orderService) {
                        this.orderService = orderService;
                    }

                    @GetMapping("/new")
                    public String newOrderForm() {
                        return "orders/new";
                    }

                    @PostMapping
                    public String createOrder(@RequestParam String customerId, Model model) {
                        model.addAttribute("order", orderService.createOrder(customerId));
                        return "orders/detail";
                    }
                }
                """,
                f"{BASE_PACKAGE_PATH}/order/service/OrderService.java": """
                package com.example.market.order.service;

                import com.example.market.order.mapper.OrderMapper;
                import java.util.Map;
                import org.springframework.stereotype.Service;
                import org.springframework.transaction.annotation.Transactional;

                @Service
                public class OrderService {
                    private final OrderMapper orderMapper;

                    public OrderService(OrderMapper orderMapper) {
                        this.orderMapper = orderMapper;
                    }

                    @Transactional
                    public Map<String, Object> createOrder(String customerId) {
                        orderMapper.insertOrder(customerId, "PAYMENT_WAITING");
                        return orderMapper.selectLatestOrder(customerId);
                    }
                }
                """,
                f"{BASE_PACKAGE_PATH}/order/mapper/OrderMapper.java": """
                package com.example.market.order.mapper;

                import java.util.Map;
                import org.apache.ibatis.annotations.Mapper;
                import org.apache.ibatis.annotations.Param;

                @Mapper
                public interface OrderMapper {
                    void insertOrder(@Param("customerId") String customerId, @Param("status") String status);
                    Map<String, Object> selectLatestOrder(@Param("customerId") String customerId);
                    void updateOrderStatus(@Param("orderId") long orderId, @Param("status") String status);
                }
                """,
                f"{RESOURCE_MAPPER_PATH}/OrderMapper.xml": """
                <?xml version="1.0" encoding="UTF-8" ?>
                <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                  "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                <mapper namespace="com.example.market.order.mapper.OrderMapper">
                    <insert id="insertOrder">
                        insert into orders(customer_id, status, created_at)
                        values (#{customerId}, #{status}, current_timestamp)
                    </insert>
                    <select id="selectLatestOrder" resultType="map">
                        select order_id, customer_id, status, created_at
                        from orders
                        where customer_id = #{customerId}
                        order by order_id desc
                        limit 1
                    </select>
                    <update id="updateOrderStatus">
                        update orders set status = #{status}, updated_at = current_timestamp
                        where order_id = #{orderId}
                    </update>
                </mapper>
                """,
                f"{WEBAPP_PATH}/orders/new.jsp": """
                <%@ page contentType="text/html;charset=UTF-8" %>
                <form method="post" action="/orders">
                    <label>Customer ID</label>
                    <input name="customerId" />
                    <button type="submit">Create order</button>
                </form>
                """,
            },
        ),
        CommitStep(
            "Reserve inventory with MyBatis mapper",
            DEVELOPERS["inventory"],
            3,
            {
                f"{BASE_PACKAGE_PATH}/inventory/controller/InventoryController.java": """
                package com.example.market.inventory.controller;

                import com.example.market.inventory.service.InventoryService;
                import org.springframework.web.bind.annotation.PostMapping;
                import org.springframework.web.bind.annotation.RequestMapping;
                import org.springframework.web.bind.annotation.RequestParam;
                import org.springframework.web.bind.annotation.RestController;

                @RestController
                @RequestMapping("/inventory")
                public class InventoryController {
                    private final InventoryService inventoryService;

                    public InventoryController(InventoryService inventoryService) {
                        this.inventoryService = inventoryService;
                    }

                    @PostMapping("/reservations")
                    public String reserve(@RequestParam String sku, @RequestParam int quantity) {
                        return inventoryService.reserve(sku, quantity);
                    }
                }
                """,
                f"{BASE_PACKAGE_PATH}/inventory/service/InventoryService.java": """
                package com.example.market.inventory.service;

                import com.example.market.inventory.mapper.InventoryMapper;
                import org.springframework.stereotype.Service;
                import org.springframework.transaction.annotation.Transactional;

                @Service
                public class InventoryService {
                    private final InventoryMapper inventoryMapper;

                    public InventoryService(InventoryMapper inventoryMapper) {
                        this.inventoryMapper = inventoryMapper;
                    }

                    @Transactional
                    public String reserve(String sku, int quantity) {
                        int available = inventoryMapper.selectAvailableQuantity(sku);
                        if (available < quantity) {
                            return "SHORTAGE";
                        }
                        inventoryMapper.insertReservation(sku, quantity);
                        return "RESERVED";
                    }
                }
                """,
                f"{BASE_PACKAGE_PATH}/inventory/mapper/InventoryMapper.java": """
                package com.example.market.inventory.mapper;

                import org.apache.ibatis.annotations.Mapper;
                import org.apache.ibatis.annotations.Param;

                @Mapper
                public interface InventoryMapper {
                    int selectAvailableQuantity(@Param("sku") String sku);
                    void insertReservation(@Param("sku") String sku, @Param("quantity") int quantity);
                }
                """,
                f"{RESOURCE_MAPPER_PATH}/InventoryMapper.xml": """
                <?xml version="1.0" encoding="UTF-8" ?>
                <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                  "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                <mapper namespace="com.example.market.inventory.mapper.InventoryMapper">
                    <select id="selectAvailableQuantity" resultType="int">
                        select available_quantity from inventory where sku = #{sku}
                    </select>
                    <insert id="insertReservation">
                        insert into inventory_reservations(sku, quantity, reserved_at)
                        values (#{sku}, #{quantity}, current_timestamp)
                    </insert>
                </mapper>
                """,
            },
        ),
        CommitStep(
            "Add payment authorization flow",
            DEVELOPERS["payment"],
            5,
            {
                f"{BASE_PACKAGE_PATH}/payment/controller/PaymentController.java": """
                package com.example.market.payment.controller;

                import com.example.market.payment.service.PaymentService;
                import org.springframework.web.bind.annotation.PostMapping;
                import org.springframework.web.bind.annotation.RequestMapping;
                import org.springframework.web.bind.annotation.RequestParam;
                import org.springframework.web.bind.annotation.RestController;

                @RestController
                @RequestMapping("/payments")
                public class PaymentController {
                    private final PaymentService paymentService;

                    public PaymentController(PaymentService paymentService) {
                        this.paymentService = paymentService;
                    }

                    @PostMapping("/authorize")
                    public String authorize(@RequestParam long orderId, @RequestParam int amount) {
                        return paymentService.authorize(orderId, amount);
                    }
                }
                """,
                f"{BASE_PACKAGE_PATH}/payment/service/PaymentService.java": """
                package com.example.market.payment.service;

                import com.example.market.order.mapper.OrderMapper;
                import com.example.market.payment.mapper.PaymentMapper;
                import org.springframework.stereotype.Service;
                import org.springframework.transaction.annotation.Transactional;

                @Service
                public class PaymentService {
                    private final PaymentMapper paymentMapper;
                    private final OrderMapper orderMapper;

                    public PaymentService(PaymentMapper paymentMapper, OrderMapper orderMapper) {
                        this.paymentMapper = paymentMapper;
                        this.orderMapper = orderMapper;
                    }

                    @Transactional
                    public String authorize(long orderId, int amount) {
                        if (amount <= 0) {
                            return "REJECTED";
                        }
                        paymentMapper.insertPayment(orderId, amount, "AUTHORIZED");
                        orderMapper.updateOrderStatus(orderId, "PAID");
                        return "AUTHORIZED";
                    }
                }
                """,
                f"{BASE_PACKAGE_PATH}/payment/mapper/PaymentMapper.java": """
                package com.example.market.payment.mapper;

                import org.apache.ibatis.annotations.Mapper;
                import org.apache.ibatis.annotations.Param;

                @Mapper
                public interface PaymentMapper {
                    void insertPayment(@Param("orderId") long orderId, @Param("amount") int amount, @Param("status") String status);
                }
                """,
                f"{RESOURCE_MAPPER_PATH}/PaymentMapper.xml": """
                <?xml version="1.0" encoding="UTF-8" ?>
                <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                  "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                <mapper namespace="com.example.market.payment.mapper.PaymentMapper">
                    <insert id="insertPayment">
                        insert into payments(order_id, amount, status, authorized_at)
                        values (#{orderId}, #{amount}, #{status}, current_timestamp)
                    </insert>
                </mapper>
                """,
            },
        ),
        CommitStep(
            "Track order status transition history",
            DEVELOPERS["order"],
            6,
            {
                f"{BASE_PACKAGE_PATH}/order/service/OrderStatusService.java": """
                package com.example.market.order.service;

                import com.example.market.order.mapper.OrderStatusMapper;
                import java.util.Set;
                import org.springframework.stereotype.Service;
                import org.springframework.transaction.annotation.Transactional;

                @Service
                public class OrderStatusService {
                    private static final Set<String> ALLOWED_STATUS = Set.of(
                        "PAYMENT_WAITING", "PAID", "PACKING", "SHIPPED", "DONE", "CANCELED"
                    );
                    private final OrderStatusMapper orderStatusMapper;

                    public OrderStatusService(OrderStatusMapper orderStatusMapper) {
                        this.orderStatusMapper = orderStatusMapper;
                    }

                    @Transactional
                    public void changeStatus(long orderId, String status) {
                        if (!ALLOWED_STATUS.contains(status)) {
                            throw new IllegalArgumentException("unknown order status");
                        }
                        orderStatusMapper.updateStatus(orderId, status);
                        orderStatusMapper.insertStatusHistory(orderId, status);
                    }
                }
                """,
                f"{BASE_PACKAGE_PATH}/order/mapper/OrderStatusMapper.java": """
                package com.example.market.order.mapper;

                import org.apache.ibatis.annotations.Mapper;
                import org.apache.ibatis.annotations.Param;

                @Mapper
                public interface OrderStatusMapper {
                    void updateStatus(@Param("orderId") long orderId, @Param("status") String status);
                    void insertStatusHistory(@Param("orderId") long orderId, @Param("status") String status);
                }
                """,
                f"{RESOURCE_MAPPER_PATH}/OrderStatusMapper.xml": """
                <?xml version="1.0" encoding="UTF-8" ?>
                <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                  "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                <mapper namespace="com.example.market.order.mapper.OrderStatusMapper">
                    <update id="updateStatus">
                        update orders set status = #{status}, updated_at = current_timestamp where order_id = #{orderId}
                    </update>
                    <insert id="insertStatusHistory">
                        insert into order_status_history(order_id, status, changed_at)
                        values (#{orderId}, #{status}, current_timestamp)
                    </insert>
                </mapper>
                """,
                "src/test/java/com/example/market/order/OrderStatusServiceTest.java": """
                package com.example.market.order;

                import static org.junit.jupiter.api.Assertions.assertTrue;
                import org.junit.jupiter.api.Test;

                class OrderStatusServiceTest {
                    @Test
                    void documentsShippingStatus() {
                        assertTrue("SHIPPED".length() > 0);
                    }
                }
                """,
            },
        ),
        CommitStep(
            "Add sales report aggregation query",
            DEVELOPERS["inventory"],
            8,
            {
                f"{BASE_PACKAGE_PATH}/report/controller/ReportController.java": """
                package com.example.market.report.controller;

                import com.example.market.report.service.SalesReportService;
                import org.springframework.stereotype.Controller;
                import org.springframework.ui.Model;
                import org.springframework.web.bind.annotation.GetMapping;
                import org.springframework.web.bind.annotation.RequestMapping;

                @Controller
                @RequestMapping("/reports")
                public class ReportController {
                    private final SalesReportService salesReportService;

                    public ReportController(SalesReportService salesReportService) {
                        this.salesReportService = salesReportService;
                    }

                    @GetMapping("/sales")
                    public String sales(Model model) {
                        model.addAttribute("summary", salesReportService.summarize());
                        return "reports/sales";
                    }
                }
                """,
                f"{BASE_PACKAGE_PATH}/report/service/SalesReportService.java": """
                package com.example.market.report.service;

                import com.example.market.report.mapper.ReportMapper;
                import java.util.Map;
                import org.springframework.stereotype.Service;

                @Service
                public class SalesReportService {
                    private final ReportMapper reportMapper;

                    public SalesReportService(ReportMapper reportMapper) {
                        this.reportMapper = reportMapper;
                    }

                    public Map<String, Object> summarize() {
                        return reportMapper.selectDailySalesSummary();
                    }
                }
                """,
                f"{BASE_PACKAGE_PATH}/report/mapper/ReportMapper.java": """
                package com.example.market.report.mapper;

                import java.util.Map;
                import org.apache.ibatis.annotations.Mapper;

                @Mapper
                public interface ReportMapper {
                    Map<String, Object> selectDailySalesSummary();
                }
                """,
                f"{RESOURCE_MAPPER_PATH}/ReportMapper.xml": """
                <?xml version="1.0" encoding="UTF-8" ?>
                <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                  "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                <mapper namespace="com.example.market.report.mapper.ReportMapper">
                    <select id="selectDailySalesSummary" resultType="map">
                        select current_date as sales_date,
                               count(*) as order_count,
                               coalesce(sum(amount), 0) as authorized_amount
                        from payments
                        where status = 'AUTHORIZED'
                    </select>
                </mapper>
                """,
                f"{WEBAPP_PATH}/reports/sales.jsp": """
                <%@ page contentType="text/html;charset=UTF-8" %>
                <h1>Sales report</h1>
                <p>${summary.authorizedAmount}</p>
                """,
            },
        ),
        CommitStep(
            "Build operations dashboard JSP",
            DEVELOPERS["payment"],
            10,
            {
                f"{BASE_PACKAGE_PATH}/dashboard/controller/DashboardController.java": """
                package com.example.market.dashboard.controller;

                import com.example.market.dashboard.service.DashboardService;
                import org.springframework.stereotype.Controller;
                import org.springframework.ui.Model;
                import org.springframework.web.bind.annotation.GetMapping;

                @Controller
                public class DashboardController {
                    private final DashboardService dashboardService;

                    public DashboardController(DashboardService dashboardService) {
                        this.dashboardService = dashboardService;
                    }

                    @GetMapping("/dashboard")
                    public String dashboard(Model model) {
                        model.addAttribute("summary", dashboardService.summary());
                        return "dashboard/index";
                    }
                }
                """,
                f"{BASE_PACKAGE_PATH}/dashboard/service/DashboardService.java": """
                package com.example.market.dashboard.service;

                import com.example.market.dashboard.mapper.DashboardMapper;
                import java.util.Map;
                import org.springframework.stereotype.Service;

                @Service
                public class DashboardService {
                    private final DashboardMapper dashboardMapper;

                    public DashboardService(DashboardMapper dashboardMapper) {
                        this.dashboardMapper = dashboardMapper;
                    }

                    public Map<String, Object> summary() {
                        return dashboardMapper.selectOperationSummary();
                    }
                }
                """,
                f"{BASE_PACKAGE_PATH}/dashboard/mapper/DashboardMapper.java": """
                package com.example.market.dashboard.mapper;

                import java.util.Map;
                import org.apache.ibatis.annotations.Mapper;

                @Mapper
                public interface DashboardMapper {
                    Map<String, Object> selectOperationSummary();
                }
                """,
                f"{RESOURCE_MAPPER_PATH}/DashboardMapper.xml": """
                <?xml version="1.0" encoding="UTF-8" ?>
                <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                  "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                <mapper namespace="com.example.market.dashboard.mapper.DashboardMapper">
                    <select id="selectOperationSummary" resultType="map">
                        select 12 as open_orders, 2 as inventory_shortage, 4 as payment_waiting
                    </select>
                </mapper>
                """,
                f"{WEBAPP_PATH}/dashboard/index.jsp": """
                <%@ page contentType="text/html;charset=UTF-8" %>
                <main class="dashboard">
                    <h1>운영 대시보드</h1>
                    <section>Open orders: ${summary.openOrders}</section>
                    <section>Inventory shortage: ${summary.inventoryShortage}</section>
                    <section>Payment waiting: ${summary.paymentWaiting}</section>
                </main>
                """,
                "src/main/webapp/resources/js/dashboard.js": """
                function refreshDashboard() {
                    console.log("dashboard refresh requested");
                }
                """,
                "src/main/webapp/resources/css/dashboard.css": """
                .dashboard {
                    display: grid;
                    gap: 16px;
                }
                """,
            },
        ),
        CommitStep(
            "Add QA checklist for Spring MyBatis flows",
            DEVELOPERS["qa"],
            11,
            {
                "docs/qa-checklist.md": """
                # QA checklist

                - 주문 접수 화면에서 고객 ID 입력 후 주문이 생성된다.
                - 재고 부족 시 예약 없이 SHORTAGE가 반환된다.
                - 결제 승인 후 주문 상태가 PAID로 변경된다.
                - 매출 현황과 운영 대시보드가 MyBatis 집계 결과를 표시한다.
                """,
                "src/test/java/com/example/market/dashboard/DashboardServiceTest.java": """
                package com.example.market.dashboard;

                import static org.junit.jupiter.api.Assertions.assertNotNull;
                import org.junit.jupiter.api.Test;

                class DashboardServiceTest {
                    @Test
                    void dashboardViewNameIsDocumented() {
                        assertNotNull("dashboard/index");
                    }
                }
                """,
            },
        ),
    ]


def create_repo(target_path: Path, force: bool = False) -> None:
    if target_path.exists():
        if not force:
            raise RuntimeError(f"{target_path} already exists. Use --force to recreate it.")
        if target_path.resolve().parent != _repo_default_path().parent.resolve():
            raise RuntimeError("Refusing to remove a target outside the expected C:\\dev sibling directory.")
        shutil.rmtree(target_path, onerror=_remove_readonly)

    target_path.mkdir(parents=True)
    _run(["git", "init"], cwd=target_path)
    _run(["git", "config", "core.autocrlf", "false"], cwd=target_path)
    _program_csv(target_path)

    start_at = datetime(2026, 5, 4, 9, 30, tzinfo=KST)
    for step in _commit_steps():
        _commit(target_path, step, start_at)

    developers, programs, plan = generate_sample_data(
        target_path,
        use_existing_program_csv=True,
        program_csv_path=target_path / "샘플_프로그램목록.csv",
    )
    developers = _apply_developer_profiles(developers)
    write_excel(target_path / "advisor_uploads", developers, programs, plan)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a Spring MyBatis sample repo for AI Commit Advisor.")
    parser.add_argument("--target-path", default=str(_repo_default_path()), help="Target Git repo path.")
    parser.add_argument("--force", action="store_true", help="Recreate the target when it already exists.")
    args = parser.parse_args()

    target_path = Path(args.target_path).resolve()
    create_repo(target_path, force=args.force)
    print(f"Created Spring MyBatis sample target repo: {target_path}")
    print(f"Program CSV: {target_path / '샘플_프로그램목록.csv'}")
    print(f"Upload Excel files: {target_path / 'advisor_uploads'}")


if __name__ == "__main__":
    main()
