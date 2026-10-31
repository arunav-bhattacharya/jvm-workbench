package workbench.generics.l05.demo

/** Function types: in on the parameter, out on the result. (P) -> R is Function1<in P, out R>. */
fun main() {
    val auditAll: (PaymentEvent) -> Unit = { println("audit ${it.paymentId}") }
    val describe: (PaymentEvent) -> String = { "event ${it.paymentId}" }

    val onCard: (CardAuthorized) -> Unit = auditAll          // takes more general input: fine
    val label: (CardAuthorized) -> Any = describe             // in on the left, out on the right: fine
    onCard(CardAuthorized("pay_7", 4_200))
    println(label(CardAuthorized("pay_8", 10)))

    // Wrong move. Uncomment, predict the error, then run.
    // val tooBroad: (PaymentEvent) -> Unit = onCard
}

/** The sign rule: uncomment ONE member at a time. Which are legal in a class declared `in T`? */
interface Inbox<in T> {
    fun accept(item: T)                          // in-position: fine
    fun acceptAll(items: List<T>)                // List<out E> inside a parameter: in x out = in, fine
    // fun peek(): T                             // 1
    // fun forEachPending(f: (T) -> Unit)        // 2
    // fun filterWith(p: (T) -> Boolean): Inbox<T>   // 3
}
