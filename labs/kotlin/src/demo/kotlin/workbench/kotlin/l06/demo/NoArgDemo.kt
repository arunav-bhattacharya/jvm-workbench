package workbench.kotlin.l06.demo

import workbench.kotlin.NoArgEntity

/** no-arg adds a zero-argument constructor that only Java and reflection can call. */
@NoArgEntity
class LedgerRow(val id: String, var amountMinor: Long) {
    var note: String = "default-note"
}

fun main() {
    // the way an ORM builds an empty entity before it fills in the columns
    val blank = LedgerRow::class.java.getDeclaredConstructor().newInstance()
    println("blank.amountMinor = ${blank.amountMinor}")
    println("blank.note is null: ${(blank.note as String?) == null}")   // declared String, holds null
    println("normal note = ${LedgerRow("row-1", 100).note}")

    // Wrong move. Uncomment, predict, run.
    // val direct = LedgerRow()
}
