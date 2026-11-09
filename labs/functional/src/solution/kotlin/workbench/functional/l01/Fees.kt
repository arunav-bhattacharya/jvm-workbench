package workbench.functional.l01

import java.math.BigDecimal
import java.math.RoundingMode
import java.time.Clock
import java.time.LocalTime
import java.util.Collections

/** The fee rules for instant payouts. A plain value: nothing in it can change after it is built. */
data class FeeRates(
    val percent: BigDecimal,       // 0.015 means 1.5 %
    val minimum: BigDecimal,       // never charge less than this
    val lateSurcharge: BigDecimal, // added when the payout is requested at or after the cut-off
    val cutoff: LocalTime,         // the same-day payout cut-off
)

/** The rates most merchants pay. */
val STANDARD_RATES = FeeRates(BigDecimal("0.015"), BigDecimal("0.50"), BigDecimal("1.00"), LocalTime.of(16, 0))

/** Global and mutable: an admin endpoint swaps the rates while the service runs. */
object FeeConfig {
    @Volatile
    var rates: FeeRates = STANDARD_RATES
}

/** Every quote writes one line here. In production the lines go to the audit service. */
object AuditLog {
    val lines: MutableList<String> = Collections.synchronizedList(ArrayList())
}

// The functional core: the result depends only on the three arguments, and the call changes nothing.
fun payoutFee(amount: BigDecimal, rates: FeeRates, requestedAt: LocalTime): BigDecimal {
    val base = amount.multiply(rates.percent).setScale(2, RoundingMode.HALF_EVEN)
    val atLeastMinimum = base.max(rates.minimum)
    val late = !requestedAt.isBefore(rates.cutoff)          // at or after the cut-off
    return if (late) atLeastMinimum + rates.lateSurcharge else atLeastMinimum   // if is an expression
}

// Also pure: it decides WHAT to log. Writing it is the shell's job.
fun auditLine(amount: BigDecimal, fee: BigDecimal, requestedAt: LocalTime): String =
    "payout fee $fee on $amount at $requestedAt"

// The imperative shell: gather the inputs, call the core, perform the effect. No decisions left here.
fun quotePayoutFee(amount: BigDecimal, clock: Clock = Clock.systemDefaultZone()): BigDecimal {
    val rates = FeeConfig.rates                 // 1. read the hidden inputs once
    val now = LocalTime.now(clock)
    val fee = payoutFee(amount, rates, now)     // 2. decide, purely
    AuditLog.lines.add(auditLine(amount, fee, now))   // 3. do the effect
    return fee
}
