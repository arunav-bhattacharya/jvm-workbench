package workbench.functional.l05

/**
 * The acquirer's settlement API. Pages are numbered from 0. Each call is an HTTP request,
 * and an empty page means there are no more.
 */
fun interface SettlementApi {
    fun page(number: Int): List<Payment>
}

/**
 * Every payment the API holds, page after page, as a lazy [Sequence]. Build it with `sequence { }`:
 * - fetch nothing until someone asks for the first payment;
 * - fetch page n + 1 only once every payment of page n has been handed out;
 * - stop at the first empty page, and never ask for the page after it.
 */
fun allSettlements(api: SettlementApi): Sequence<Payment> =
    TODO("sequence { ... yieldAll(page) ... }")
