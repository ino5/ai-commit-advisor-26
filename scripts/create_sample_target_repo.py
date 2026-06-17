"""Create a synthetic Spring MVC + MyBatis project for AI Commit Advisor demos."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import textwrap
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

try:
    from scripts.generate_sample_development_data import generate_sample_data, write_excel
except ModuleNotFoundError:
    from generate_sample_development_data import generate_sample_data, write_excel


KST = timezone(timedelta(hours=9))
SAMPLE_HISTORY_START_AT = datetime(2026, 4, 25, 9, 30, tzinfo=KST)
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
    {
        "프로그램ID": "SMP-CPN-001",
        "프로그램명": "쿠폰 할인",
        "주요기능": "coupon",
        "주요URL/화면": "/coupons/apply",
        "기능설명": "주문 금액에 적용할 쿠폰 할인 가능 여부와 할인 금액을 계산합니다.",
        "Controller": "CouponController.java",
        "Service": "CouponDiscountService.java",
        "Mapper/Repository": "CouponMapper.java, CouponMapper.xml",
    },
    {
        "프로그램ID": "SMP-SET-001",
        "프로그램명": "정산 내보내기",
        "주요기능": "settlement",
        "주요URL/화면": "/settlements/export",
        "기능설명": "결제 승인 내역을 정산 파일로 생성하고 운영자가 다운로드할 수 있게 합니다.",
        "Controller": "SettlementController.java",
        "Service": "SettlementExportService.java",
        "Mapper/Repository": "SettlementMapper.java, SettlementMapper.xml",
    },
]


STANDARD_TERM_ROWS = [
    {
        "term_type": "표준용어",
        "korean_term": "결제금액",
        "english_term": "payment amount",
        "abbreviation": "pay amt",
        "description": "결제 요청 금액. 코드에서는 amount, DB에서는 payments.amount로 표현됩니다.",
    },
    {
        "term_type": "표준용어",
        "korean_term": "결제승인",
        "english_term": "payment authorization",
        "abbreviation": "pay auth",
        "description": "결제 요청을 승인하고 주문 상태를 PAID로 변경하는 업무입니다.",
    },
    {
        "term_type": "표준용어",
        "korean_term": "주문번호",
        "english_term": "order number",
        "abbreviation": "ord no",
        "description": "주문 식별자. 샘플 코드에서는 orderId와 order_id로 표현됩니다.",
    },
    {
        "term_type": "표준용어",
        "korean_term": "주문상태",
        "english_term": "order status",
        "abbreviation": "ord stat",
        "description": "주문 진행 상태. PAYMENT_WAITING, PAID, PACKING 같은 값으로 표현됩니다.",
    },
    {
        "term_type": "표준용어",
        "korean_term": "쿠폰할인",
        "english_term": "coupon discount",
        "abbreviation": "cpn dc",
        "description": "쿠폰 정책에 따른 할인 가능 여부와 할인 금액 계산입니다.",
    },
    {
        "term_type": "표준용어",
        "korean_term": "재고예약",
        "english_term": "inventory reservation",
        "abbreviation": "inv rsv",
        "description": "주문 생성 전후 판매 가능 수량을 확인하고 재고를 예약하는 업무입니다.",
    },
    {
        "term_type": "표준용어",
        "korean_term": "정산내보내기",
        "english_term": "settlement export",
        "abbreviation": "stl exp",
        "description": "결제 승인 내역을 정산 파일로 생성해 운영자가 내려받는 업무입니다.",
    },
    {
        "term_type": "표준용어",
        "korean_term": "매출현황",
        "english_term": "sales report",
        "abbreviation": "sales rpt",
        "description": "일자별 주문 금액, 결제 상태, 취소 금액 집계 화면입니다.",
    },
    {
        "term_type": "표준단어",
        "korean_term": "승인",
        "english_term": "authorization",
        "abbreviation": "auth",
        "description": "결제 승인과 권한 승인 문맥에서 사용하는 표준단어입니다.",
    },
    {
        "term_type": "표준단어",
        "korean_term": "검증",
        "english_term": "validation",
        "abbreviation": "vld",
        "description": "입력값과 업무 규칙 확인을 의미합니다.",
    },
    {
        "term_type": "표준용어",
        "korean_term": "운영대시보드",
        "english_term": "operations dashboard",
        "abbreviation": "ops dash",
        "description": "주문, 결제대기, 재고부족, stale payment warning을 모아 운영자가 확인하는 화면입니다.",
    },
    {
        "term_type": "표준용어",
        "korean_term": "결제감사",
        "english_term": "payment audit",
        "abbreviation": "pay audit",
        "description": "결제 승인/거절 이벤트를 payment_audit_logs에 남기는 감사 기록입니다.",
    },
    {
        "term_type": "표준용어",
        "korean_term": "최소주문금액",
        "english_term": "minimum order amount",
        "abbreviation": "min ord amt",
        "description": "쿠폰 적용 전 주문 금액이 넘어야 하는 기준이며 CouponMapper.xml의 minimum_order_amount와 연결됩니다.",
    },
    {
        "term_type": "표준단어",
        "korean_term": "감사",
        "english_term": "audit",
        "abbreviation": "audit",
        "description": "운영자 다운로드와 결제 처리 이력을 추적하는 기록을 의미합니다.",
    },
]


def _repo_default_path() -> Path:
    return Path(__file__).resolve().parents[2] / "ai-advisor-sample-shop"


def _run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True, env=env)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


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


def _standard_terms_excel(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(STANDARD_TERM_ROWS).to_excel(output_dir / "sample_standard_terms.xlsx", index=False)


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


def _apply_demo_plan_overrides(plan: pd.DataFrame) -> pd.DataFrame:
    result = plan.copy()
    overrides = {
        "SMP-CPN-001": {
            "developer_id": "DEV_JIEUN_LEE",
            "planned_start_date": datetime(2026, 5, 18).date(),
            "planned_end_date": datetime(2026, 5, 28).date(),
            "actual_start_date": datetime(2026, 5, 23).date(),
            "actual_end_date": None,
            "status": "지연",
            "progress_rate": 80,
        },
        "SMP-SET-001": {
            "developer_id": "",
            "planned_start_date": datetime(2026, 5, 12).date(),
            "planned_end_date": datetime(2026, 5, 24).date(),
            "actual_start_date": None,
            "actual_end_date": None,
            "status": "지연",
            "progress_rate": 45,
        },
    }
    for program_id, values in overrides.items():
        mask = result["program_id"] == program_id
        for column, value in values.items():
            result.loc[mask, column] = value
    return result


def _commit_steps() -> list[CommitStep]:
    base_steps = [
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
                ".gitignore": """
                advisor_uploads/
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
                f"{BASE_PACKAGE_PATH}/common/ProgramBaseline.java": """
                package com.example.market.common;

                import java.util.List;

                public final class ProgramBaseline {
                    public static final List<String> FIRST_RELEASE_PROGRAMS = List.of(
                        "SMP-ORD-001",
                        "SMP-ORD-002",
                        "SMP-INV-001",
                        "SMP-PAY-001",
                        "SMP-RPT-001",
                        "SMP-UI-001"
                    );
                    public static final String PAYMENT_APPROVAL_TARGET_STATUS = "PAID";
                    public static final String DASHBOARD_PERFORMANCE_REVIEW = "operations dashboard aggregation";

                    private ProgramBaseline() {
                    }
                }
                """,
                f"{BASE_PACKAGE_PATH}/common/LayerPolicy.java": """
                package com.example.market.common;

                public final class LayerPolicy {
                    public static final String CONTROLLER = "request and screen entry point";
                    public static final String SERVICE = "transaction and business rule boundary";
                    public static final String MAPPER_XML = "SQL and result mapping boundary";

                    private LayerPolicy() {
                    }
                }
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

                    @Transactional
                    public void markPaid(long orderId) {
                        changeStatus(orderId, "PAID");
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
            "Add QA probes for Spring MyBatis flows",
            DEVELOPERS["qa"],
            11,
            {
                "src/test/java/com/example/market/dashboard/DashboardServiceTest.java": """
                package com.example.market.dashboard;

                import static org.junit.jupiter.api.Assertions.assertNotNull;
                import org.junit.jupiter.api.Test;

                class DashboardServiceTest {
                    @Test
                    void dashboardViewNameIsStable() {
                        assertNotNull("dashboard/index");
                    }
                }
                """,
            },
        ),
    ]

    base_steps.extend(
        [
            CommitStep(
                "Validate customer and cart input for order creation",
                DEVELOPERS["order"],
                12,
                {
                    f"{BASE_PACKAGE_PATH}/order/service/OrderService.java": """
                    package com.example.market.order.service;

                    import com.example.market.order.mapper.OrderMapper;
                    import java.util.Map;
                    import org.springframework.stereotype.Service;
                    import org.springframework.transaction.annotation.Transactional;
                    import org.springframework.util.StringUtils;

                    @Service
                    public class OrderService {
                        private final OrderMapper orderMapper;

                        public OrderService(OrderMapper orderMapper) {
                            this.orderMapper = orderMapper;
                        }

                        @Transactional
                        public Map<String, Object> createOrder(String customerId) {
                            if (!StringUtils.hasText(customerId)) {
                                throw new IllegalArgumentException("customerId is required");
                            }
                            orderMapper.insertOrder(customerId.trim(), OrderStatus.PAYMENT_WAITING.code());
                            return orderMapper.selectLatestOrder(customerId.trim());
                        }
                    }
                    """,
                    f"{BASE_PACKAGE_PATH}/order/service/OrderStatus.java": """
                    package com.example.market.order.service;

                    public enum OrderStatus {
                        PAYMENT_WAITING,
                        PAID,
                        PACKING,
                        SHIPPED,
                        DONE,
                        CANCELED;

                        public String code() {
                            return name();
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Expose inventory shortage message for operations dashboard",
                DEVELOPERS["inventory"],
                13,
                {
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
                            if (sku == null || sku.isBlank() || quantity <= 0) {
                                return "INVALID_REQUEST";
                            }
                            int available = inventoryMapper.selectAvailableQuantity(sku);
                            if (available < quantity) {
                                inventoryMapper.insertShortageSignal(sku, quantity, available);
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
                        void insertShortageSignal(@Param("sku") String sku, @Param("requested") int requested, @Param("available") int available);
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
                        <insert id="insertShortageSignal">
                            insert into inventory_shortage_signals(sku, requested_quantity, available_quantity, detected_at)
                            values (#{sku}, #{requested}, #{available}, current_timestamp)
                        </insert>
                    </mapper>
                    """,
                },
            ),
            CommitStep(
                "Relax partner payment validation for pilot channel",
                DEVELOPERS["payment"],
                14,
                {
                    f"{BASE_PACKAGE_PATH}/payment/service/PaymentService.java": """
                    package com.example.market.payment.service;

                    import com.example.market.order.service.OrderStatusService;
                    import com.example.market.payment.mapper.PaymentMapper;
                    import org.springframework.stereotype.Service;
                    import org.springframework.transaction.annotation.Transactional;

                    @Service
                    public class PaymentService {
                        private final PaymentMapper paymentMapper;
                        private final OrderStatusService orderStatusService;

                        public PaymentService(PaymentMapper paymentMapper, OrderStatusService orderStatusService) {
                            this.paymentMapper = paymentMapper;
                            this.orderStatusService = orderStatusService;
                        }

                        @Transactional
                        public String authorize(long orderId, int amount) {
                            if (amount < 0) {
                                return "REJECTED";
                            }
                            paymentMapper.insertPayment(orderId, amount, "AUTHORIZED");
                            orderStatusService.markPaid(orderId);
                            return "AUTHORIZED";
                        }
                    }
                    """,
                    "src/test/java/com/example/market/payment/PaymentPilotAuthorizationRiskTest.java": """
                    package com.example.market.payment;

                    import static org.junit.jupiter.api.Assertions.assertEquals;
                    import org.junit.jupiter.api.Test;

                    class PaymentPilotAuthorizationRiskTest {
                        @Test
                        void zeroAmountWouldStillBecomeAuthorizedInPilotChange() {
                            int amount = 0;
                            String status = amount < 0 ? "REJECTED" : "AUTHORIZED";
                            assertEquals("AUTHORIZED", status);
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Reject zero and negative payment amounts",
                DEVELOPERS["payment"],
                15,
                {
                    f"{BASE_PACKAGE_PATH}/payment/service/PaymentService.java": """
                    package com.example.market.payment.service;

                    import com.example.market.order.service.OrderStatusService;
                    import com.example.market.payment.mapper.PaymentMapper;
                    import org.springframework.stereotype.Service;
                    import org.springframework.transaction.annotation.Transactional;

                    @Service
                    public class PaymentService {
                        private final PaymentMapper paymentMapper;
                        private final OrderStatusService orderStatusService;

                        public PaymentService(PaymentMapper paymentMapper, OrderStatusService orderStatusService) {
                            this.paymentMapper = paymentMapper;
                            this.orderStatusService = orderStatusService;
                        }

                        @Transactional
                        public String authorize(long orderId, int amount) {
                            if (amount <= 0) {
                                return "REJECTED";
                            }
                            paymentMapper.insertPayment(orderId, amount, "AUTHORIZED");
                            orderStatusService.markPaid(orderId);
                            return "AUTHORIZED";
                        }
                    }
                    """,
                    "src/test/java/com/example/market/payment/PaymentServiceTest.java": """
                    package com.example.market.payment;

                    import static org.junit.jupiter.api.Assertions.assertEquals;
                    import org.junit.jupiter.api.Test;

                    class PaymentServiceTest {
                        @Test
                        void zeroAmountPaymentMustBeRejected() {
                            assertEquals("REJECTED", "REJECTED");
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Block invalid order status transitions",
                DEVELOPERS["order"],
                16,
                {
                    f"{BASE_PACKAGE_PATH}/order/service/OrderStatusService.java": """
                    package com.example.market.order.service;

                    import com.example.market.order.mapper.OrderStatusMapper;
                    import java.util.Map;
                    import java.util.Set;
                    import org.springframework.stereotype.Service;
                    import org.springframework.transaction.annotation.Transactional;

                    @Service
                    public class OrderStatusService {
                        private static final Map<String, Set<String>> ALLOWED_TRANSITIONS = Map.of(
                            "PAYMENT_WAITING", Set.of("PAID", "CANCELED"),
                            "PAID", Set.of("PACKING", "CANCELED"),
                            "PACKING", Set.of("SHIPPED"),
                            "SHIPPED", Set.of("DONE")
                        );
                        private final OrderStatusMapper orderStatusMapper;

                        public OrderStatusService(OrderStatusMapper orderStatusMapper) {
                            this.orderStatusMapper = orderStatusMapper;
                        }

                        @Transactional
                        public void changeStatus(long orderId, String currentStatus, String nextStatus) {
                            if (!ALLOWED_TRANSITIONS.getOrDefault(currentStatus, Set.of()).contains(nextStatus)) {
                                throw new IllegalArgumentException("invalid order status transition");
                            }
                            orderStatusMapper.updateStatus(orderId, nextStatus);
                            orderStatusMapper.insertStatusHistory(orderId, nextStatus);
                        }

                        @Transactional
                        public void markPaid(long orderId) {
                            changeStatus(orderId, "PAYMENT_WAITING", "PAID");
                        }
                    }
                    """,
                    "src/test/java/com/example/market/order/OrderStatusTransitionPolicyTest.java": """
                    package com.example.market.order;

                    import static org.junit.jupiter.api.Assertions.assertFalse;
                    import static org.junit.jupiter.api.Assertions.assertTrue;
                    import java.util.Map;
                    import java.util.Set;
                    import org.junit.jupiter.api.Test;

                    class OrderStatusTransitionPolicyTest {
                        @Test
                        void paymentWaitingCanMoveOnlyToPaidOrCanceled() {
                            Map<String, Set<String>> allowed = Map.of("PAYMENT_WAITING", Set.of("PAID", "CANCELED"));
                            assertTrue(allowed.get("PAYMENT_WAITING").contains("PAID"));
                            assertFalse(allowed.get("PAYMENT_WAITING").contains("SHIPPED"));
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Exclude canceled payments from sales totals",
                DEVELOPERS["inventory"],
                17,
                {
                    f"{RESOURCE_MAPPER_PATH}/ReportMapper.xml": """
                    <?xml version="1.0" encoding="UTF-8" ?>
                    <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                      "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                    <mapper namespace="com.example.market.report.mapper.ReportMapper">
                        <select id="selectDailySalesSummary" resultType="map">
                            select current_date as sales_date,
                                   count(*) as order_count,
                                   coalesce(sum(case when status = 'AUTHORIZED' then amount else 0 end), 0) as authorized_amount,
                                   coalesce(sum(case when status = 'CANCELED' then amount else 0 end), 0) as canceled_amount
                            from payments
                            where status in ('AUTHORIZED', 'CANCELED')
                        </select>
                    </mapper>
                    """,
                    "src/test/java/com/example/market/report/SalesReportPolicyTest.java": """
                    package com.example.market.report;

                    import static org.junit.jupiter.api.Assertions.assertEquals;
                    import org.junit.jupiter.api.Test;

                    class SalesReportPolicyTest {
                        @Test
                        void canceledPaymentIsTrackedOutsideAuthorizedAmount() {
                            int authorizedAmount = 10000;
                            int canceledAmount = 3000;
                            assertEquals(10000, authorizedAmount);
                            assertEquals(3000, canceledAmount);
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Add dashboard refresh summary endpoint",
                DEVELOPERS["payment"],
                18,
                {
                    f"{BASE_PACKAGE_PATH}/dashboard/controller/DashboardApiController.java": """
                    package com.example.market.dashboard.controller;

                    import com.example.market.dashboard.service.DashboardService;
                    import java.util.Map;
                    import org.springframework.web.bind.annotation.GetMapping;
                    import org.springframework.web.bind.annotation.RequestMapping;
                    import org.springframework.web.bind.annotation.RestController;

                    @RestController
                    @RequestMapping("/dashboard/api")
                    public class DashboardApiController {
                        private final DashboardService dashboardService;

                        public DashboardApiController(DashboardService dashboardService) {
                            this.dashboardService = dashboardService;
                        }

                        @GetMapping("/summary")
                        public Map<String, Object> summary() {
                            return dashboardService.summary();
                        }
                    }
                    """,
                    "src/main/webapp/resources/js/dashboard.js": """
                    async function refreshDashboard() {
                        const response = await fetch("/dashboard/api/summary");
                        return response.json();
                    }
                    """,
                },
            ),
            CommitStep(
                "Show payment waiting and inventory shortage indicators",
                DEVELOPERS["inventory"],
                19,
                {
                    f"{RESOURCE_MAPPER_PATH}/DashboardMapper.xml": """
                    <?xml version="1.0" encoding="UTF-8" ?>
                    <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                      "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                    <mapper namespace="com.example.market.dashboard.mapper.DashboardMapper">
                        <select id="selectOperationSummary" resultType="map">
                            select
                                (select count(*) from orders where status in ('PAYMENT_WAITING', 'PAID', 'PACKING')) as open_orders,
                                (select count(*) from inventory_shortage_signals where resolved_yn = 'N') as inventory_shortage,
                                (select count(*) from orders where status = 'PAYMENT_WAITING') as payment_waiting
                        </select>
                    </mapper>
                    """,
                    f"{WEBAPP_PATH}/dashboard/index.jsp": """
                    <%@ page contentType="text/html;charset=UTF-8" %>
                    <main class="dashboard">
                        <h1>운영 대시보드</h1>
                        <section data-metric="open-orders">Open orders: ${summary.openOrders}</section>
                        <section data-metric="inventory-shortage">Inventory shortage: ${summary.inventoryShortage}</section>
                        <section data-metric="payment-waiting">Payment waiting: ${summary.paymentWaiting}</section>
                    </main>
                    """,
                },
            ),
            CommitStep(
                "Add service tests for order and inventory validation",
                DEVELOPERS["qa"],
                20,
                {
                    "src/test/java/com/example/market/order/OrderServiceTest.java": """
                    package com.example.market.order;

                    import static org.junit.jupiter.api.Assertions.assertThrows;
                    import org.junit.jupiter.api.Test;

                    class OrderServiceTest {
                        @Test
                        void blankCustomerIdIsRejected() {
                            assertThrows(IllegalArgumentException.class, () -> {
                                throw new IllegalArgumentException("customerId is required");
                            });
                        }
                    }
                    """,
                    "src/test/java/com/example/market/inventory/InventoryServiceTest.java": """
                    package com.example.market.inventory;

                    import static org.junit.jupiter.api.Assertions.assertEquals;
                    import org.junit.jupiter.api.Test;

                    class InventoryServiceTest {
                        @Test
                        void invalidQuantityIsRejected() {
                            assertEquals("INVALID_REQUEST", "INVALID_REQUEST");
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Extract shared order status constants",
                DEVELOPERS["order"],
                21,
                {
                    f"{BASE_PACKAGE_PATH}/common/OrderStatuses.java": """
                    package com.example.market.common;

                    public final class OrderStatuses {
                        public static final String PAYMENT_WAITING = "PAYMENT_WAITING";
                        public static final String PAID = "PAID";
                        public static final String PACKING = "PACKING";
                        public static final String SHIPPED = "SHIPPED";
                        public static final String DONE = "DONE";
                        public static final String CANCELED = "CANCELED";

                        private OrderStatuses() {
                        }
                    }
                    """,
                    f"{BASE_PACKAGE_PATH}/order/service/OrderStatusService.java": """
                    package com.example.market.order.service;

                    import static com.example.market.common.OrderStatuses.CANCELED;
                    import static com.example.market.common.OrderStatuses.DONE;
                    import static com.example.market.common.OrderStatuses.PACKING;
                    import static com.example.market.common.OrderStatuses.PAID;
                    import static com.example.market.common.OrderStatuses.PAYMENT_WAITING;
                    import static com.example.market.common.OrderStatuses.SHIPPED;

                    import com.example.market.order.mapper.OrderStatusMapper;
                    import java.util.Map;
                    import java.util.Set;
                    import org.springframework.stereotype.Service;
                    import org.springframework.transaction.annotation.Transactional;

                    @Service
                    public class OrderStatusService {
                        private static final Map<String, Set<String>> ALLOWED_TRANSITIONS = Map.of(
                            PAYMENT_WAITING, Set.of(PAID, CANCELED),
                            PAID, Set.of(PACKING, CANCELED),
                            PACKING, Set.of(SHIPPED),
                            SHIPPED, Set.of(DONE)
                        );
                        private final OrderStatusMapper orderStatusMapper;

                        public OrderStatusService(OrderStatusMapper orderStatusMapper) {
                            this.orderStatusMapper = orderStatusMapper;
                        }

                        @Transactional
                        public void changeStatus(long orderId, String currentStatus, String nextStatus) {
                            if (!ALLOWED_TRANSITIONS.getOrDefault(currentStatus, Set.of()).contains(nextStatus)) {
                                throw new IllegalArgumentException("invalid order status transition");
                            }
                            orderStatusMapper.updateStatus(orderId, nextStatus);
                            orderStatusMapper.insertStatusHistory(orderId, nextStatus);
                        }

                        @Transactional
                        public void markPaid(long orderId) {
                            changeStatus(orderId, PAYMENT_WAITING, PAID);
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Normalize MyBatis result mappings for reports",
                DEVELOPERS["inventory"],
                22,
                {
                    f"{RESOURCE_MAPPER_PATH}/ReportMapper.xml": """
                    <?xml version="1.0" encoding="UTF-8" ?>
                    <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                      "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                    <mapper namespace="com.example.market.report.mapper.ReportMapper">
                        <resultMap id="dailySalesSummaryMap" type="map">
                            <result column="sales_date" property="salesDate"/>
                            <result column="order_count" property="orderCount"/>
                            <result column="authorized_amount" property="authorizedAmount"/>
                            <result column="canceled_amount" property="canceledAmount"/>
                        </resultMap>
                        <select id="selectDailySalesSummary" resultMap="dailySalesSummaryMap">
                            select current_date as sales_date,
                                   count(*) as order_count,
                                   coalesce(sum(case when status = 'AUTHORIZED' then amount else 0 end), 0) as authorized_amount,
                                   coalesce(sum(case when status = 'CANCELED' then amount else 0 end), 0) as canceled_amount
                            from payments
                            where status in ('AUTHORIZED', 'CANCELED')
                        </select>
                    </mapper>
                    """,
                },
            ),
            CommitStep(
                "Add basic operator role check for dashboard and reports",
                DEVELOPERS["pl"],
                23,
                {
                    f"{BASE_PACKAGE_PATH}/security/OperatorRoleGuard.java": """
                    package com.example.market.security;

                    import org.springframework.stereotype.Component;
                    import org.springframework.util.StringUtils;

                    @Component
                    public class OperatorRoleGuard {
                        public void requireOperator(String role) {
                            if (!StringUtils.hasText(role) || !"OPERATOR".equals(role)) {
                                throw new SecurityException("operator role is required");
                            }
                        }
                    }
                    """,
                    f"{BASE_PACKAGE_PATH}/dashboard/controller/DashboardController.java": """
                    package com.example.market.dashboard.controller;

                    import com.example.market.dashboard.service.DashboardService;
                    import com.example.market.security.OperatorRoleGuard;
                    import org.springframework.stereotype.Controller;
                    import org.springframework.ui.Model;
                    import org.springframework.web.bind.annotation.GetMapping;
                    import org.springframework.web.bind.annotation.RequestHeader;

                    @Controller
                    public class DashboardController {
                        private final DashboardService dashboardService;
                        private final OperatorRoleGuard operatorRoleGuard;

                        public DashboardController(DashboardService dashboardService, OperatorRoleGuard operatorRoleGuard) {
                            this.dashboardService = dashboardService;
                            this.operatorRoleGuard = operatorRoleGuard;
                        }

                        @GetMapping("/dashboard")
                        public String dashboard(@RequestHeader(name = "X-Operator-Role", required = false) String role, Model model) {
                            operatorRoleGuard.requireOperator(role);
                            model.addAttribute("summary", dashboardService.summary());
                            return "dashboard/index";
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Add coupon discount service skeleton",
                DEVELOPERS["payment"],
                24,
                {
                    f"{BASE_PACKAGE_PATH}/coupon/controller/CouponController.java": """
                    package com.example.market.coupon.controller;

                    import com.example.market.coupon.service.CouponDiscountService;
                    import org.springframework.web.bind.annotation.PostMapping;
                    import org.springframework.web.bind.annotation.RequestMapping;
                    import org.springframework.web.bind.annotation.RequestParam;
                    import org.springframework.web.bind.annotation.RestController;

                    @RestController
                    @RequestMapping("/coupons")
                    public class CouponController {
                        private final CouponDiscountService couponDiscountService;

                        public CouponController(CouponDiscountService couponDiscountService) {
                            this.couponDiscountService = couponDiscountService;
                        }

                        @PostMapping("/apply")
                        public int apply(@RequestParam String couponCode, @RequestParam int orderAmount) {
                            return couponDiscountService.previewDiscount(couponCode, orderAmount);
                        }
                    }
                    """,
                    f"{BASE_PACKAGE_PATH}/coupon/service/CouponDiscountService.java": """
                    package com.example.market.coupon.service;

                    import org.springframework.stereotype.Service;

                    @Service
                    public class CouponDiscountService {
                        public int previewDiscount(String couponCode, int orderAmount) {
                            if (couponCode == null || couponCode.isBlank()) {
                                return 0;
                            }
                            // TODO: connect coupon policy table and expiration validation before release.
                            return Math.min(orderAmount / 10, 5000);
                        }
                    }
                    """,
                    f"{BASE_PACKAGE_PATH}/coupon/service/CouponPolicyStatus.java": """
                    package com.example.market.coupon.service;

                    public final class CouponPolicyStatus {
                        public static final boolean EXPIRATION_VALIDATION_READY = false;
                        public static final boolean MINIMUM_ORDER_AMOUNT_READY = false;
                        public static final boolean DUPLICATE_USE_VALIDATION_READY = false;

                        private CouponPolicyStatus() {
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Add ambiguous order status helper rename",
                DEVELOPERS["order"],
                25,
                {
                    f"{BASE_PACKAGE_PATH}/order/service/OrderStatusNames.java": """
                    package com.example.market.order.service;

                    public final class OrderStatusNames {
                        public static String displayName(String status) {
                            return switch (status) {
                                case "PAYMENT_WAITING" -> "Payment waiting";
                                case "PAID" -> "Paid";
                                case "PACKING" -> "Packing";
                                case "SHIPPED" -> "Shipped";
                                case "DONE" -> "Done";
                                case "CANCELED" -> "Canceled";
                                default -> "Unknown";
                            };
                        }

                        private OrderStatusNames() {
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Add payment and inventory business rule constants",
                DEVELOPERS["pl"],
                26,
                {
                    f"{BASE_PACKAGE_PATH}/common/BusinessRuleCatalog.java": """
                    package com.example.market.common;

                    public final class BusinessRuleCatalog {
                        private static final String PAID_STATUS = "PAID";
                        public static final String PAYMENT_AMOUNT_MUST_BE_POSITIVE = "payment amount must be positive";
                        public static final String PAYMENT_AUTHORIZATION_TARGET_ORDER_STATUS = PAID_STATUS;
                        public static final String INVENTORY_SHORTAGE_SIGNAL = "inventory shortage signal";

                        private BusinessRuleCatalog() {
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Change dashboard summary query across operations modules",
                DEVELOPERS["payment"],
                27,
                {
                    f"{RESOURCE_MAPPER_PATH}/DashboardMapper.xml": """
                    <?xml version="1.0" encoding="UTF-8" ?>
                    <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                      "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                    <mapper namespace="com.example.market.dashboard.mapper.DashboardMapper">
                        <select id="selectOperationSummary" resultType="map">
                            select count(o.order_id) as open_orders,
                                   count(s.signal_id) as inventory_shortage,
                                   count(p.payment_id) as payment_waiting
                            from orders o
                            left join inventory_shortage_signals s on s.resolved_yn = 'N'
                            left join payments p on p.order_id = o.order_id
                            where o.status in ('PAYMENT_WAITING', 'PAID', 'PACKING')
                        </select>
                    </mapper>
                    """,
                    "src/test/java/com/example/market/dashboard/DashboardSummaryJoinRiskTest.java": """
                    package com.example.market.dashboard;

                    import static org.junit.jupiter.api.Assertions.assertTrue;
                    import org.junit.jupiter.api.Test;

                    class DashboardSummaryJoinRiskTest {
                        @Test
                        void joinBasedCountsNeedIndependentMetricDefinitions() {
                            String query = "count(o.order_id), count(s.signal_id), count(p.payment_id)";
                            assertTrue(query.contains("count(o.order_id)"));
                            assertTrue(query.contains("count(s.signal_id)"));
                            assertTrue(query.contains("count(p.payment_id)"));
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Fix dashboard summary over-counting",
                DEVELOPERS["inventory"],
                28,
                {
                    f"{RESOURCE_MAPPER_PATH}/DashboardMapper.xml": """
                    <?xml version="1.0" encoding="UTF-8" ?>
                    <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                      "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                    <mapper namespace="com.example.market.dashboard.mapper.DashboardMapper">
                        <select id="selectOperationSummary" resultType="map">
                            select
                                (select count(*) from orders where status in ('PAYMENT_WAITING', 'PAID', 'PACKING')) as open_orders,
                                (select count(*) from inventory_shortage_signals where resolved_yn = 'N') as inventory_shortage,
                                (select count(*) from orders where status = 'PAYMENT_WAITING') as payment_waiting
                        </select>
                    </mapper>
                    """,
                    "src/test/java/com/example/market/dashboard/DashboardSummaryQueryTest.java": """
                    package com.example.market.dashboard;

                    import static org.junit.jupiter.api.Assertions.assertTrue;
                    import org.junit.jupiter.api.Test;

                    class DashboardSummaryQueryTest {
                        @Test
                        void summaryUsesIndependentSubqueries() {
                            assertTrue("subquery".length() > 0);
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Add release verification source probes",
                DEVELOPERS["qa"],
                29,
                {
                    "src/test/java/com/example/market/release/ReleaseVerificationProbeTest.java": """
                    package com.example.market.release;

                    import static org.junit.jupiter.api.Assertions.assertFalse;
                    import static org.junit.jupiter.api.Assertions.assertTrue;
                    import org.junit.jupiter.api.Test;

                    class ReleaseVerificationProbeTest {
                        @Test
                        void completedAndIncompleteReleaseSignalsAreSeparated() {
                            assertTrue("payment amount validation".contains("payment"));
                            assertTrue("dashboard independent subqueries".contains("dashboard"));
                            assertFalse(Boolean.getBoolean("coupon.minimum.order.ready"));
                            assertFalse(Boolean.getBoolean("settlement.export.ready"));
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Add payment audit trail mapper",
                DEVELOPERS["payment"],
                30,
                {
                    f"{BASE_PACKAGE_PATH}/payment/mapper/PaymentAuditMapper.java": """
                    package com.example.market.payment.mapper;

                    import org.apache.ibatis.annotations.Mapper;
                    import org.apache.ibatis.annotations.Param;

                    @Mapper
                    public interface PaymentAuditMapper {
                        void insertAudit(@Param("orderId") long orderId, @Param("eventType") String eventType, @Param("message") String message);
                    }
                    """,
                    f"{RESOURCE_MAPPER_PATH}/PaymentAuditMapper.xml": """
                    <?xml version="1.0" encoding="UTF-8" ?>
                    <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                      "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                    <mapper namespace="com.example.market.payment.mapper.PaymentAuditMapper">
                        <insert id="insertAudit">
                            insert into payment_audit_logs(order_id, event_type, message, created_at)
                            values (#{orderId}, #{eventType}, #{message}, current_timestamp)
                        </insert>
                    </mapper>
                    """,
                },
            ),
            CommitStep(
                "Add coupon mapper draft without policy enforcement",
                DEVELOPERS["payment"],
                31,
                {
                    f"{BASE_PACKAGE_PATH}/coupon/mapper/CouponMapper.java": """
                    package com.example.market.coupon.mapper;

                    import java.util.Map;
                    import org.apache.ibatis.annotations.Mapper;
                    import org.apache.ibatis.annotations.Param;

                    @Mapper
                    public interface CouponMapper {
                        Map<String, Object> selectCoupon(@Param("couponCode") String couponCode);
                    }
                    """,
                    f"{RESOURCE_MAPPER_PATH}/CouponMapper.xml": """
                    <?xml version="1.0" encoding="UTF-8" ?>
                    <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                      "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                    <mapper namespace="com.example.market.coupon.mapper.CouponMapper">
                        <select id="selectCoupon" resultType="map">
                            select coupon_code,
                                   discount_type,
                                   discount_value,
                                   expires_at,
                                   minimum_order_amount,
                                   duplicate_use_yn,
                                   member_grade
                            from coupons
                            where coupon_code = #{couponCode}
                        </select>
                    </mapper>
                    """,
                },
            ),
            CommitStep(
                "Log payment authorization audit events",
                DEVELOPERS["payment"],
                32,
                {
                    f"{BASE_PACKAGE_PATH}/payment/service/PaymentService.java": """
                    package com.example.market.payment.service;

                    import com.example.market.order.service.OrderStatusService;
                    import com.example.market.payment.mapper.PaymentAuditMapper;
                    import com.example.market.payment.mapper.PaymentMapper;
                    import org.springframework.stereotype.Service;
                    import org.springframework.transaction.annotation.Transactional;

                    @Service
                    public class PaymentService {
                        private final PaymentMapper paymentMapper;
                        private final PaymentAuditMapper paymentAuditMapper;
                        private final OrderStatusService orderStatusService;

                        public PaymentService(PaymentMapper paymentMapper, PaymentAuditMapper paymentAuditMapper, OrderStatusService orderStatusService) {
                            this.paymentMapper = paymentMapper;
                            this.paymentAuditMapper = paymentAuditMapper;
                            this.orderStatusService = orderStatusService;
                        }

                        @Transactional
                        public String authorize(long orderId, int amount) {
                            if (amount <= 0) {
                                paymentAuditMapper.insertAudit(orderId, "REJECTED", "payment amount must be positive");
                                return "REJECTED";
                            }
                            paymentMapper.insertPayment(orderId, amount, "AUTHORIZED");
                            paymentAuditMapper.insertAudit(orderId, "AUTHORIZED", "payment authorization completed");
                            orderStatusService.markPaid(orderId);
                            return "AUTHORIZED";
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Reject excessive payment amount requests",
                DEVELOPERS["payment"],
                33,
                {
                    f"{BASE_PACKAGE_PATH}/payment/service/PaymentService.java": """
                    package com.example.market.payment.service;

                    import com.example.market.order.service.OrderStatusService;
                    import com.example.market.payment.mapper.PaymentAuditMapper;
                    import com.example.market.payment.mapper.PaymentMapper;
                    import org.springframework.stereotype.Service;
                    import org.springframework.transaction.annotation.Transactional;

                    @Service
                    public class PaymentService {
                        private static final int MAX_AUTHORIZATION_AMOUNT = 10_000_000;
                        private final PaymentMapper paymentMapper;
                        private final PaymentAuditMapper paymentAuditMapper;
                        private final OrderStatusService orderStatusService;

                        public PaymentService(PaymentMapper paymentMapper, PaymentAuditMapper paymentAuditMapper, OrderStatusService orderStatusService) {
                            this.paymentMapper = paymentMapper;
                            this.paymentAuditMapper = paymentAuditMapper;
                            this.orderStatusService = orderStatusService;
                        }

                        @Transactional
                        public String authorize(long orderId, int amount) {
                            if (amount <= 0) {
                                paymentAuditMapper.insertAudit(orderId, "REJECTED", "payment amount must be positive");
                                return "REJECTED";
                            }
                            if (amount > MAX_AUTHORIZATION_AMOUNT) {
                                paymentAuditMapper.insertAudit(orderId, "REJECTED", "payment amount exceeds single authorization limit");
                                return "REJECTED";
                            }
                            paymentMapper.insertPayment(orderId, amount, "AUTHORIZED");
                            paymentAuditMapper.insertAudit(orderId, "AUTHORIZED", "payment authorization completed");
                            orderStatusService.markPaid(orderId);
                            return "AUTHORIZED";
                        }
                    }
                    """,
                    "src/test/java/com/example/market/payment/PaymentLimitRuleTest.java": """
                    package com.example.market.payment;

                    import static org.junit.jupiter.api.Assertions.assertEquals;
                    import org.junit.jupiter.api.Test;

                    class PaymentLimitRuleTest {
                        @Test
                        void excessivePaymentAmountIsRejected() {
                            int maxAuthorizationAmount = 10_000_000;
                            int requestedAmount = 10_000_001;
                            String result = requestedAmount > maxAuthorizationAmount ? "REJECTED" : "AUTHORIZED";
                            assertEquals("REJECTED", result);
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Add inventory reservation release flow",
                DEVELOPERS["inventory"],
                34,
                {
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
                            if (sku == null || sku.isBlank() || quantity <= 0) {
                                return "REJECTED";
                            }
                            int available = inventoryMapper.selectAvailableQuantity(sku);
                            if (available < quantity) {
                                inventoryMapper.insertShortageSignal(sku, quantity);
                                return "SHORTAGE";
                            }
                            inventoryMapper.insertReservation(sku, quantity);
                            return "RESERVED";
                        }

                        @Transactional
                        public void release(String sku, int quantity, String reason) {
                            inventoryMapper.insertReservationRelease(sku, quantity, reason);
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
                        void insertShortageSignal(@Param("sku") String sku, @Param("quantity") int quantity);
                        void insertReservationRelease(@Param("sku") String sku, @Param("quantity") int quantity, @Param("reason") String reason);
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
                        <insert id="insertShortageSignal">
                            insert into inventory_shortage_signals(sku, requested_quantity, resolved_yn, created_at)
                            values (#{sku}, #{quantity}, 'N', current_timestamp)
                        </insert>
                        <insert id="insertReservationRelease">
                            insert into inventory_reservation_releases(sku, quantity, reason, released_at)
                            values (#{sku}, #{quantity}, #{reason}, current_timestamp)
                        </insert>
                    </mapper>
                    """,
                },
            ),
            CommitStep(
                "Add inventory release validation test",
                DEVELOPERS["qa"],
                35,
                {
                    "src/test/java/com/example/market/inventory/InventoryReleaseTest.java": """
                    package com.example.market.inventory;

                    import static org.junit.jupiter.api.Assertions.assertEquals;
                    import org.junit.jupiter.api.Test;

                    class InventoryReleaseTest {
                        @Test
                        void releaseReasonIsRequiredInOperationsChecklist() {
                            assertEquals("payment canceled", "payment canceled");
                        }
                    }
                    """,
                    "src/test/java/com/example/market/inventory/InventoryReleaseOperationsTest.java": """
                    package com.example.market.inventory;

                    import static org.junit.jupiter.api.Assertions.assertEquals;
                    import static org.junit.jupiter.api.Assertions.assertTrue;
                    import org.junit.jupiter.api.Test;

                    class InventoryReleaseOperationsTest {
                        @Test
                        void releaseAndShortageSignalsStaySeparate() {
                            assertEquals("payment canceled", "payment canceled");
                            assertTrue("unresolved shortage signals".contains("shortage"));
                            assertTrue("dashboard shortage counts".contains("dashboard"));
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Add dashboard stale payment warning",
                DEVELOPERS["payment"],
                36,
                {
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
                            Map<String, Object> summary = dashboardMapper.selectOperationSummary();
                            summary.put("stalePaymentWarning", dashboardMapper.countStalePaymentWaitingOrders());
                            return summary;
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
                        int countStalePaymentWaitingOrders();
                    }
                    """,
                    f"{RESOURCE_MAPPER_PATH}/DashboardMapper.xml": """
                    <?xml version="1.0" encoding="UTF-8" ?>
                    <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                      "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                    <mapper namespace="com.example.market.dashboard.mapper.DashboardMapper">
                        <select id="selectOperationSummary" resultType="map">
                            select
                                (select count(*) from orders where status in ('PAYMENT_WAITING', 'PAID', 'PACKING')) as open_orders,
                                (select count(*) from inventory_shortage_signals where resolved_yn = 'N') as inventory_shortage,
                                (select count(*) from orders where status = 'PAYMENT_WAITING') as payment_waiting
                        </select>
                        <select id="countStalePaymentWaitingOrders" resultType="int">
                            select count(*)
                            from orders
                            where status = 'PAYMENT_WAITING'
                              and created_at < current_timestamp - interval '2 hours'
                        </select>
                    </mapper>
                    """,
                },
            ),
            CommitStep(
                "Add settlement export readiness contract",
                DEVELOPERS["pm"],
                37,
                {
                    f"{BASE_PACKAGE_PATH}/settlement/service/SettlementReadiness.java": """
                    package com.example.market.settlement.service;

                    public final class SettlementReadiness {
                        public static final boolean EXPORT_FILE_WRITER_READY = false;
                        public static final boolean AUTHORIZED_PAYMENT_QUERY_READY = false;
                        public static final boolean REVERSAL_ROW_QUERY_READY = false;
                        public static final boolean OPERATOR_DOWNLOAD_AUDIT_READY = false;

                        private SettlementReadiness() {
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Add settlement export controller stub",
                DEVELOPERS["payment"],
                38,
                {
                    f"{BASE_PACKAGE_PATH}/settlement/controller/SettlementController.java": """
                    package com.example.market.settlement.controller;

                    import org.springframework.web.bind.annotation.GetMapping;
                    import org.springframework.web.bind.annotation.RequestMapping;
                    import org.springframework.web.bind.annotation.RestController;

                    @RestController
                    @RequestMapping("/settlements")
                    public class SettlementController {
                        @GetMapping("/export")
                        public String export() {
                            return "NOT_READY";
                        }
                    }
                    """,
                    "src/test/java/com/example/market/settlement/SettlementNotReadyTest.java": """
                    package com.example.market.settlement;

                    import static org.junit.jupiter.api.Assertions.assertEquals;
                    import static org.junit.jupiter.api.Assertions.assertFalse;
                    import org.junit.jupiter.api.Test;

                    class SettlementNotReadyTest {
                        @Test
                        void controllerStubDoesNotMeanSettlementExportIsComplete() {
                            assertEquals("NOT_READY", "NOT_READY");
                            assertFalse(Boolean.getBoolean("settlement.export.file.writer.ready"));
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Keep return request outside release source scope",
                DEVELOPERS["pl"],
                39,
                {
                    "src/test/java/com/example/market/planning/ReturnRequestScopeTest.java": """
                    package com.example.market.planning;

                    import static org.junit.jupiter.api.Assertions.assertFalse;
                    import java.util.Set;
                    import org.junit.jupiter.api.Test;

                    class ReturnRequestScopeTest {
                        @Test
                        void returnRequestIsNotInCurrentReleaseProgramIds() {
                            Set<String> releasePrograms = Set.of("SMP-ORD-001", "SMP-PAY-001", "SMP-CPN-001", "SMP-SET-001");
                            assertFalse(releasePrograms.contains("SMP-RET-001"));
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Add sales report tax amount column",
                DEVELOPERS["inventory"],
                40,
                {
                    f"{RESOURCE_MAPPER_PATH}/ReportMapper.xml": """
                    <?xml version="1.0" encoding="UTF-8" ?>
                    <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                      "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                    <mapper namespace="com.example.market.report.mapper.ReportMapper">
                        <resultMap id="dailySalesSummaryMap" type="map">
                            <result column="sales_date" property="salesDate"/>
                            <result column="order_count" property="orderCount"/>
                            <result column="authorized_amount" property="authorizedAmount"/>
                            <result column="canceled_amount" property="canceledAmount"/>
                            <result column="tax_amount" property="taxAmount"/>
                        </resultMap>
                        <select id="selectDailySalesSummary" resultMap="dailySalesSummaryMap">
                            select current_date as sales_date,
                                   count(*) as order_count,
                                   coalesce(sum(case when status = 'AUTHORIZED' then amount else 0 end), 0) as authorized_amount,
                                   coalesce(sum(case when status = 'CANCELED' then amount else 0 end), 0) as canceled_amount,
                                   coalesce(sum(amount / 10), 0) as tax_amount
                            from payments
                            where status in ('AUTHORIZED', 'CANCELED')
                        </select>
                    </mapper>
                    """,
                },
            ),
            CommitStep(
                "Fix sales report tax calculation for canceled payments",
                DEVELOPERS["inventory"],
                41,
                {
                    f"{RESOURCE_MAPPER_PATH}/ReportMapper.xml": """
                    <?xml version="1.0" encoding="UTF-8" ?>
                    <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                      "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                    <mapper namespace="com.example.market.report.mapper.ReportMapper">
                        <resultMap id="dailySalesSummaryMap" type="map">
                            <result column="sales_date" property="salesDate"/>
                            <result column="order_count" property="orderCount"/>
                            <result column="authorized_amount" property="authorizedAmount"/>
                            <result column="canceled_amount" property="canceledAmount"/>
                            <result column="tax_amount" property="taxAmount"/>
                        </resultMap>
                        <select id="selectDailySalesSummary" resultMap="dailySalesSummaryMap">
                            select current_date as sales_date,
                                   count(*) as order_count,
                                   coalesce(sum(case when status = 'AUTHORIZED' then amount else 0 end), 0) as authorized_amount,
                                   coalesce(sum(case when status = 'CANCELED' then amount else 0 end), 0) as canceled_amount,
                                   coalesce(sum(case when status = 'AUTHORIZED' then amount / 10 else 0 end), 0) as tax_amount
                            from payments
                            where status in ('AUTHORIZED', 'CANCELED')
                        </select>
                    </mapper>
                    """,
                    "src/test/java/com/example/market/report/SalesReportTaxTest.java": """
                    package com.example.market.report;

                    import static org.junit.jupiter.api.Assertions.assertTrue;
                    import org.junit.jupiter.api.Test;

                    class SalesReportTaxTest {
                        @Test
                        void canceledPaymentsDoNotIncreaseTaxAmount() {
                            assertTrue("AUTHORIZED".contains("AUTH"));
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Add coupon expiration validation",
                DEVELOPERS["payment"],
                42,
                {
                    f"{BASE_PACKAGE_PATH}/coupon/service/CouponDiscountService.java": """
                    package com.example.market.coupon.service;

                    import com.example.market.coupon.mapper.CouponMapper;
                    import java.time.LocalDate;
                    import java.util.Map;
                    import org.springframework.stereotype.Service;

                    @Service
                    public class CouponDiscountService {
                        private final CouponMapper couponMapper;

                        public CouponDiscountService(CouponMapper couponMapper) {
                            this.couponMapper = couponMapper;
                        }

                        public int previewDiscount(String couponCode, int orderAmount) {
                            if (couponCode == null || couponCode.isBlank() || orderAmount <= 0) {
                                return 0;
                            }
                            Map<String, Object> coupon = couponMapper.selectCoupon(couponCode);
                            if (coupon == null || coupon.get("expires_at") == null) {
                                return 0;
                            }
                            LocalDate expiresAt = LocalDate.parse(String.valueOf(coupon.get("expires_at")));
                            if (expiresAt.isBefore(LocalDate.now())) {
                                return 0;
                            }
                            return Math.min(orderAmount / 10, 5000);
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Expose coupon minimum order gap in source",
                DEVELOPERS["payment"],
                43,
                {
                    f"{BASE_PACKAGE_PATH}/coupon/service/CouponPolicyStatus.java": """
                    package com.example.market.coupon.service;

                    public final class CouponPolicyStatus {
                        public static final boolean EXPIRATION_VALIDATION_READY = true;
                        public static final boolean MINIMUM_ORDER_AMOUNT_READY = false;
                        public static final boolean DUPLICATE_USE_VALIDATION_READY = false;
                        public static final boolean MEMBER_GRADE_VALIDATION_READY = false;
                        public static final String UNREAD_COUPON_COLUMN = "minimum_order_amount";

                        private CouponPolicyStatus() {
                        }
                    }
                    """,
                    "src/test/java/com/example/market/coupon/CouponMinimumOrderGapTest.java": """
                    package com.example.market.coupon;

                    import static org.junit.jupiter.api.Assertions.assertFalse;
                    import static org.junit.jupiter.api.Assertions.assertTrue;
                    import org.junit.jupiter.api.Test;

                    class CouponMinimumOrderGapTest {
                        @Test
                        void mapperContainsMinimumOrderAmountButServiceDoesNotEnforceItYet() {
                            String mapperColumns = "coupon_code discount_type discount_value expires_at minimum_order_amount duplicate_use_yn member_grade";
                            boolean serviceComparesMinimumOrderAmount = false;
                            assertTrue(mapperColumns.contains("minimum_order_amount"));
                            assertFalse(serviceComparesMinimumOrderAmount);
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Refactor dashboard indicator names",
                DEVELOPERS["order"],
                44,
                {
                    f"{BASE_PACKAGE_PATH}/dashboard/service/DashboardIndicatorNames.java": """
                    package com.example.market.dashboard.service;

                    public final class DashboardIndicatorNames {
                        public static final String OPEN_ORDERS = "openOrders";
                        public static final String INVENTORY_SHORTAGE = "inventoryShortage";
                        public static final String PAYMENT_WAITING = "paymentWaiting";
                        public static final String STALE_PAYMENT_WARNING = "stalePaymentWarning";

                        private DashboardIndicatorNames() {
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Add operations smoke test source probe",
                DEVELOPERS["qa"],
                45,
                {
                    "src/test/java/com/example/market/operations/OperationsSmokeFlowTest.java": """
                    package com.example.market.operations;

                    import static org.junit.jupiter.api.Assertions.assertEquals;
                    import static org.junit.jupiter.api.Assertions.assertTrue;
                    import org.junit.jupiter.api.Test;

                    class OperationsSmokeFlowTest {
                        @Test
                        void smokeFlowCoversOrderInventoryPaymentDashboardAndReport() {
                            assertEquals("PAYMENT_WAITING", "PAYMENT_WAITING");
                            assertEquals("SHORTAGE", "SHORTAGE");
                            assertTrue("payment audit rows".contains("audit"));
                            assertTrue("stale payment warning count".contains("warning"));
                            assertTrue("canceled payments do not increase tax amount".contains("tax"));
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Add source evidence probes for Project Chat",
                DEVELOPERS["pl"],
                46,
                {
                    "src/test/java/com/example/market/advisor/ProjectChatSourceEvidenceTest.java": """
                    package com.example.market.advisor;

                    import static org.junit.jupiter.api.Assertions.assertTrue;
                    import java.util.List;
                    import org.junit.jupiter.api.Test;

                    class ProjectChatSourceEvidenceTest {
                        @Test
                        void sourceIdentifiersCoverRecommendedChatQuestions() {
                            List<String> identifiers = List.of(
                                "PaymentService.authorize",
                                "InventoryService.release",
                                "InventoryMapper.insertReservationRelease",
                                "SettlementReadiness.EXPORT_FILE_WRITER_READY",
                                "CouponPolicyStatus.MINIMUM_ORDER_AMOUNT_READY",
                                "DashboardMapper.countStalePaymentWaitingOrders"
                            );
                            assertTrue(identifiers.contains("PaymentService.authorize"));
                            assertTrue(identifiers.contains("CouponPolicyStatus.MINIMUM_ORDER_AMOUNT_READY"));
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Tighten settlement export source readiness",
                DEVELOPERS["pm"],
                47,
                {
                    f"{BASE_PACKAGE_PATH}/settlement/service/SettlementReadiness.java": """
                    package com.example.market.settlement.service;

                    public final class SettlementReadiness {
                        public static final boolean EXPORT_FILE_WRITER_READY = false;
                        public static final boolean AUTHORIZED_PAYMENT_QUERY_READY = false;
                        public static final boolean REVERSAL_ROW_QUERY_READY = false;
                        public static final boolean OPERATOR_DOWNLOAD_AUDIT_READY = false;
                        public static final String CURRENT_ENDPOINT_STATUS = "NOT_READY";
                        public static final String ASSIGNMENT_STATUS = "UNASSIGNED_IN_DEVELOPMENT_PLAN";

                        private SettlementReadiness() {
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Add operator audit source contract",
                DEVELOPERS["pl"],
                48,
                {
                    f"{BASE_PACKAGE_PATH}/audit/OperatorAuditEvent.java": """
                    package com.example.market.audit;

                    public class OperatorAuditEvent {
                        private final String operatorId;
                        private final String actionType;
                        private final String evidenceKey;

                        public OperatorAuditEvent(String operatorId, String actionType, String evidenceKey) {
                            this.operatorId = operatorId;
                            this.actionType = actionType;
                            this.evidenceKey = evidenceKey;
                        }

                        public String getOperatorId() {
                            return operatorId;
                        }

                        public String getActionType() {
                            return actionType;
                        }

                        public String getEvidenceKey() {
                            return evidenceKey;
                        }
                    }
                    """,
                    f"{BASE_PACKAGE_PATH}/audit/OperatorAuditMapper.java": """
                    package com.example.market.audit;

                    import org.apache.ibatis.annotations.Mapper;
                    import org.apache.ibatis.annotations.Param;

                    @Mapper
                    public interface OperatorAuditMapper {
                        void insertOperatorAudit(@Param("event") OperatorAuditEvent event);
                    }
                    """,
                    f"{RESOURCE_MAPPER_PATH}/OperatorAuditMapper.xml": """
                    <?xml version="1.0" encoding="UTF-8" ?>
                    <!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN"
                      "https://mybatis.org/dtd/mybatis-3-mapper.dtd">
                    <mapper namespace="com.example.market.audit.OperatorAuditMapper">
                        <insert id="insertOperatorAudit">
                            insert into operator_audit_events(operator_id, action_type, evidence_key, created_at)
                            values (#{event.operatorId}, #{event.actionType}, #{event.evidenceKey}, current_timestamp)
                        </insert>
                    </mapper>
                    """,
                },
            ),
            CommitStep(
                "Add final cross-module release readiness probes",
                DEVELOPERS["qa"],
                49,
                {
                    "src/test/java/com/example/market/release/CrossModuleReleaseReadinessTest.java": """
                    package com.example.market.release;

                    import static org.junit.jupiter.api.Assertions.assertFalse;
                    import static org.junit.jupiter.api.Assertions.assertTrue;
                    import org.junit.jupiter.api.Test;

                    class CrossModuleReleaseReadinessTest {
                        @Test
                        void readyWatchAndNotReadySignalsStayVisibleInSource() {
                            assertTrue("order payment audit inventory dashboard sales report".contains("payment"));
                            assertTrue("stale payment warning".contains("warning"));
                            assertFalse(Boolean.getBoolean("coupon.minimum.order.ready"));
                            assertFalse(Boolean.getBoolean("settlement.export.file.ready"));
                        }
                    }
                    """,
                },
            ),
            CommitStep(
                "Add advisor review target source probes",
                DEVELOPERS["pm"],
                50,
                {
                    "src/test/java/com/example/market/advisor/AdvisorReviewTargetProbeTest.java": """
                    package com.example.market.advisor;

                    import static org.junit.jupiter.api.Assertions.assertTrue;
                    import java.util.Map;
                    import org.junit.jupiter.api.Test;

                    class AdvisorReviewTargetProbeTest {
                        @Test
                        void reviewTargetsAreDiscoverableFromSourceAndDiffs() {
                            Map<String, String> targets = Map.of(
                                "payment-zero-amount", "PaymentService.authorize amount == 0 and order status PAID",
                                "dashboard-over-count", "DashboardMapper count(o.order_id) count(s.signal_id) count(p.payment_id)",
                                "coupon-minimum-order-gap", "CouponMapper minimum_order_amount but CouponDiscountService ignores it",
                                "settlement-not-ready", "SettlementController returns NOT_READY and SettlementReadiness flags remain false"
                            );
                            assertTrue(targets.get("payment-zero-amount").contains("PaymentService"));
                            assertTrue(targets.get("dashboard-over-count").contains("count(o.order_id)"));
                        }
                    }
                    """,
                },
            ),
        ]
    )
    return base_steps


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

    for step in _commit_steps():
        _commit(target_path, step, SAMPLE_HISTORY_START_AT)

    developers, programs, plan = generate_sample_data(
        target_path,
        use_existing_program_csv=True,
        program_csv_path=target_path / "샘플_프로그램목록.csv",
    )
    developers = _apply_developer_profiles(developers)
    plan = _apply_demo_plan_overrides(plan)
    write_excel(target_path / "advisor_uploads", developers, programs, plan)
    _standard_terms_excel(target_path / "advisor_uploads")


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
