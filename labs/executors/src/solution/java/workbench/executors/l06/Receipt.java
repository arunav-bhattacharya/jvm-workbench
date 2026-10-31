package workbench.executors.l06;

import java.math.BigDecimal;

public record Receipt(String cartId, BigDecimal amount, String currency, String chargeId) {}
