package workbench.generics.l07.demo

/** out T with a bound: Source<*> means Source<out Number>. */
interface Source<out T : Number> { fun next(): T }

/** in T: Sink<*> means Sink<in Nothing>. */
interface Sink<in T> { fun accept(item: T) }

/** invariant T: Box<*> reads as Box<out Any?> and writes as Box<in Nothing>. */
class Box<T>(var item: T)

fun peek(source: Source<*>): Number = source.next()   // the bound survives the star
fun peek(box: Box<*>): Any? = box.item

fun main() {
    val amounts: Source<Int> = object : Source<Int> { override fun next() = 1_200 }
    val audit: Sink<String> = object : Sink<String> { override fun accept(item: String) = println("audit $item") }
    val box: Box<String> = Box("EUR")

    println("peek(source) = ${peek(amounts)}, peek(box) = ${peek(box)}")

    audit.accept("pay_0")                       // through the real type: fine
    val anySink: Sink<*> = audit                // through *: nothing can be passed in
    val anyBox: Box<*> = box
    println("a Box<*> still reads: ${anyBox.item}")

    // Wrong moves. Uncomment one at a time, predict the error, then run.
    // anySink.accept("pay_1")                  // 1
    // anyBox.item = "USD"                      // 2
    // val n: Int = peek(amounts)               // 3
}
