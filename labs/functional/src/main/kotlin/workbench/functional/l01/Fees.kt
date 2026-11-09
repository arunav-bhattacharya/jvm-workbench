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

/**
 * The fee rule as a pure function. Everything it needs arrives as an argument.
 *
 * - The fee is amount x rates.percent, rounded to cents with RoundingMode.HALF_EVEN.
 * - It is never less than rates.minimum.
 * - Add rates.lateSurcharge when requestedAt is at or after rates.cutoff.
 *
 * TODO 1: write it. Do not read FeeConfig, the clock or AuditLog. Try it with `val`s and an
 * `if` expression, and no `var`.
 */
fun payoutFee(amount: BigDecimal, rates: FeeRates, requestedAt: LocalTime): BigDecimal =
    TODO("percent of the amount, at least the minimum, plus the surcharge when late")

/**
 * The audit line for one quote, built as a value. The shell writes it; this function only makes the text.
 * Format: "payout fee 3.00 on 200.00 at 15:30" (use the LocalTime's own toString for the time).
 *
 * TODO 2: write it.
 */
fun auditLine(amount: BigDecimal, fee: BigDecimal, requestedAt: LocalTime): String =
    TODO("one string template")

/**
 * The original, impure quote. It reads the clock and the global config, does the arithmetic,
 * and writes the audit log. Someone already added the Clock parameter so it could be tested at all.
 *
 * Its three tests pass already. They pin its behaviour, so your refactor can't change it by accident.
 *
 * TODO 3: once payoutFee and auditLine work, turn this into a thin shell: read the clock and the
 * config, call payoutFee, add auditLine(...) to the log, return the fee. No fee arithmetic stays here.
 */
fun quotePayoutFee(amount: BigDecimal, clock: Clock = Clock.systemDefaultZone()): BigDecimal {
    val rates = FeeConfig.rates
    val now = LocalTime.now(clock)
    var fee = amount.multiply(rates.percent).setScale(2, RoundingMode.HALF_EVEN)
    if (fee < rates.minimum) fee = rates.minimum
    if (!now.isBefore(rates.cutoff)) fee += rates.lateSurcharge
    AuditLog.lines.add("payout fee $fee on $amount at $now")
    return fee
}
