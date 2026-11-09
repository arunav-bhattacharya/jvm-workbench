package workbench.functional.l01.demo;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

/** Java twin of OrderDependentTests.kt: two tests share a static field, so their order decides the result. */
public class OrderDependentTestsJava {

    // A global the fee function reads. An admin endpoint, or a test, can change it at any time.
    static BigDecimal percent = new BigDecimal("0.015");

    // Looks harmless. But its answer depends on something that is not in its parameter list.
    static BigDecimal feeFor(BigDecimal amount) {
        return amount.multiply(percent).setScale(2, RoundingMode.HALF_EVEN);
    }

    static String standardFeeTest() {
        BigDecimal fee = feeFor(new BigDecimal("200.00"));
        return fee.equals(new BigDecimal("3.00")) ? "pass" : "FAIL (expected 3.00, got " + fee + ")";
    }

    // Sets up a premium merchant and never puts the global back.
    static String premiumMerchantTest() {
        percent = new BigDecimal("0.025");
        BigDecimal fee = feeFor(new BigDecimal("200.00"));
        return fee.equals(new BigDecimal("5.00")) ? "pass" : "FAIL (expected 5.00, got " + fee + ")";
    }

    public static void main(String[] args) {
        List<Map.Entry<String, Supplier<String>>> tests = new ArrayList<>(List.of(
                Map.entry("standardFee", OrderDependentTestsJava::standardFeeTest),
                Map.entry("premiumMerchant", OrderDependentTestsJava::premiumMerchantTest)));
        if (args.length > 0 && args[0].equals("reverse")) Collections.reverse(tests);
        for (var t : tests) System.out.println(t.getKey() + ": " + t.getValue().get());
    }
}
