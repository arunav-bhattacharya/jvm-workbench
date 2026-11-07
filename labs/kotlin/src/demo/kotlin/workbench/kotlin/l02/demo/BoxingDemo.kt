package workbench.kotlin.l02.demo

interface Priced {
    val minor: Long
}

@JvmInline
value class Amount(override val minor: Long) : Priced

class Invoice(val amount: Amount)                  // used as Amount: stored as a long

fun <T> asGeneric(x: T): Any? = x                  // used as T: boxed
fun asNullable(a: Amount?): Any? = a               // used as Amount?: boxed
fun asInterface(p: Priced): Any = p                // used as Priced: boxed

fun main() {
    val a = Amount(1_999)
    println("field in Invoice: ${Invoice::class.java.getDeclaredField("amount").type}")
    println("as generic:       ${asGeneric(a)!!.javaClass.simpleName}")
    println("as nullable:      ${asNullable(a)!!.javaClass.simpleName}")
    println("as Priced:        ${asInterface(a).javaClass.simpleName}")
    println("in a list:        ${(listOf(a)[0] as Any).javaClass.simpleName}")
    println("a == Amount(1999): ${a == Amount(1_999)}")

    // Wrong move. Uncomment, predict the error, then run.
    // println(a === Amount(1_999))
}
