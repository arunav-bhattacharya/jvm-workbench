package workbench.modernjava.l04.demo

sealed interface LedgerEntry {
    data class Charge(val paymentId: String, val amountMinor: Long) : LedgerEntry
    data class Refund(val paymentId: String, val amountMinor: Long) : LedgerEntry
    data class Fee(val reason: String, val amountMinor: Long) : LedgerEntry

    // Step 3: uncomment this class.
    // data class Chargeback(val paymentId: String, val amountMinor: Long, val caseId: String) : LedgerEntry
}

// operation 1: how the entry moves the merchant's balance
fun balanceDelta(e: LedgerEntry): Long = when (e) {
    is LedgerEntry.Charge -> e.amountMinor
    is LedgerEntry.Refund -> -e.amountMinor
    is LedgerEntry.Fee -> -e.amountMinor
}

// operation 2: the line on the merchant's statement
fun statementLine(e: LedgerEntry): String = when (e) {
    is LedgerEntry.Charge -> "payment ${e.paymentId}  +${e.amountMinor}"
    is LedgerEntry.Refund -> "refund  ${e.paymentId}  -${e.amountMinor}"
    is LedgerEntry.Fee -> "fee     ${e.reason}  -${e.amountMinor}"
}

// Step 2: write operation 3 here, isCustomerFacing(LedgerEntry), as one more when.

/** Data in data classes, operations in functions. Add an operation, then add a type, and compare the cost. */
fun main() {
    val day = listOf(LedgerEntry.Charge("pay_1", 10_000), LedgerEntry.Fee("scheme fee", 35), LedgerEntry.Refund("pay_1", 2_500))
    var balance = 0L
    for (e in day) {
        balance += balanceDelta(e)
        println(statementLine(e))
    }
    println("balance $balance")
}
