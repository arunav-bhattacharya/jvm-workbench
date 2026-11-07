package workbench.events.l01.demo.stringly

// Three handlers each read the raw fields of a message. Nothing checked the message first.

var balanceCents = 0L
var receiptsSent = 0

fun audit(fields: Map<String, String>) {
    println("audit    ${fields["type"]} ${fields["paymentId"]}")
}

fun ledger(fields: Map<String, String>) {
    if (fields["type"] == "captured") {
        val cents = fields.getValue("amountMinor").toLong()    // parsing, deep inside a handler
        balanceCents += cents
        println("ledger   +$cents, balance $balanceCents")
    }
}

fun receipts(fields: Map<String, String>) {
    if (fields["type"] == "capture") {                          // a typo the compiler can't see
        receiptsSent++
    }
}

fun main() {
    val messages = listOf(
        mapOf("type" to "captured", "paymentId" to "pay_7781", "amountMinor" to "1999"),
        mapOf("type" to "refunded", "paymentId" to "pay_7781", "amountMinor" to "500"),
        mapOf("type" to "captured", "paymentId" to "pay_7782", "amountMinor" to "12.50"),
    )
    for (m in messages) {
        try {
            audit(m)
            ledger(m)
            receipts(m)
        } catch (e: RuntimeException) {
            println("FAILED   $e")
        }
    }
    println("receipts sent: $receiptsSent")
}
