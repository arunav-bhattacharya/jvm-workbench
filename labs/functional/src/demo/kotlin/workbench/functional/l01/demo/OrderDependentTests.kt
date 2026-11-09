package workbench.functional.l01.demo

import java.math.BigDecimal
import java.math.RoundingMode

// A global the fee function reads. An admin endpoint, or a test, can change it at any time.
object Config {
    var percent = BigDecimal("0.015")
}

// Looks harmless. But its answer depends on something that is not in its parameter list.
fun feeFor(amount: BigDecimal): BigDecimal =
    amount.multiply(Config.percent).setScale(2, RoundingMode.HALF_EVEN)

// Two little "tests". The second sets up a premium merchant and never puts the global back.
fun standardFeeTest(): String {
    val fee = feeFor(BigDecimal("200.00"))
    return if (fee == BigDecimal("3.00")) "pass" else "FAIL (expected 3.00, got $fee)"
}

fun premiumMerchantTest(): String {
    Config.percent = BigDecimal("0.025")
    val fee = feeFor(BigDecimal("200.00"))
    return if (fee == BigDecimal("5.00")) "pass" else "FAIL (expected 5.00, got $fee)"
}

fun main(args: Array<String>) {
    val tests = listOf("standardFee" to ::standardFeeTest, "premiumMerchant" to ::premiumMerchantTest)
    val order = if (args.firstOrNull() == "reverse") tests.reversed() else tests
    for ((name, test) in order) println("$name: ${test()}")
}
