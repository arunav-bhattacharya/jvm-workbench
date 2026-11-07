package workbench.concurrency.scratch

import java.math.BigDecimal
import java.util.Currency
import java.util.concurrent.BlockingQueue

data class S11Merchant(val id: String, val feeBps: Int, val settlementCurrency: Currency)   // vals: final fields

fun s11Fee(m: S11Merchant): S11Merchant = m.copy(feeBps = 180)     // "changes" return a new object

class S11Rates {
    @Volatile private var rates: Map<String, BigDecimal> = emptyMap()   // an immutable map, replaced whole

    fun refresh(fresh: Map<String, BigDecimal>) {
        rates = java.util.Map.copyOf(fresh)        // build it completely, then publish it in one write
    }

    fun rate(pair: String): BigDecimal? = rates[pair]   // no lock: every map this field ever points to is immutable
}

class S11Payment(val id: String, val cents: Long)
class S11Settlement(val merchantId: String, payments: List<S11Payment>) {
    val payments: List<S11Payment> = java.util.List.copyOf(payments)   // a plain parameter, copied into a property
    // a data class can't do this: its constructor parameters ARE the properties
}

fun statementLine(p: S11Payment): String = buildString {   // the builder is local: no other thread can see it
    append(p.id).append(';').append(p.cents)
}                                                          // only the immutable String leaves

class S11Entry
fun s11HandOff(queue: BlockingQueue<List<S11Entry>>, fill: (MutableList<S11Entry>) -> Unit) {
    val batch = ArrayList<S11Entry>()                // owned by this thread
    fill(batch)
    queue.put(batch)                                 // ownership moves to whoever takes it
    // from here on, this thread never touches batch again
}

class S11Request(val tenant: String)
object S11Handler {
    private val TENANT = ThreadLocal<String>()

    fun handle(r: S11Request, process: (S11Request) -> Unit) {
        TENANT.set(r.tenant)
        try {
            process(r)                  // deep code calls TENANT.get()
        } finally {
            TENANT.remove()             // the pool thread goes back clean
        }
    }
}

class S11LineItem(val sku: String, val cents: Long)
data class S11Refund(val paymentId: String, val items: List<S11LineItem>, val reason: String)
class Refund(val paymentId: String, items: List<S11LineItem>, val reason: String) {
    val items: List<S11LineItem> = java.util.List.copyOf(items)    // copy in; unmodifiable for everyone

    fun withReason(newReason: String) = Refund(paymentId, items, newReason)   // a new object, same items
}

fun s11Sum(fees: List<BigDecimal>): BigDecimal {
    var total = BigDecimal.ZERO
    for (fee in fees) total.add(fee)                 // does nothing: the result is thrown away
    for (fee in fees) total += fee                   // right: plus() returns a new BigDecimal
    return total
}

data class Money(val cents: Long, val currency: Currency) {
    operator fun plus(other: Money): Money {           // 1. never change this; return a new value
        require(currency == other.currency) { "currency mismatch" }
        return copy(cents = Math.addExact(cents, other.cents))   // 2. overflow fails loudly
    }
}
