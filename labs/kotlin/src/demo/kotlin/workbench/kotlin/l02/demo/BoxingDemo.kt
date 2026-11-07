package workbench.kotlin.l02.demo

interface Priced {
    val minor: Long
}

@JvmInline
value class Amount(override val minor: Long) : Priced

fun asItself(a: Amount): Any = a.minor            // used as Amount: stays a long
fun <T> asGeneric(x: T): Any? = x                  // used as T: boxed
fun asNullable(a: Amount?): Any? = a               // used as Amount?: boxed
fun asInterface(p: Priced): Any = p                // used as Priced: boxed

fun main() {
    val a = Amount(1_999)
    println("as itself:   ${asItself(a).javaClass.simpleName}")
    println("as generic:  ${asGeneric(a)!!.javaClass.simpleName}")
    println("as nullable: ${asNullable(a)!!.javaClass.simpleName}")
    println("as Priced:   ${asInterface(a).javaClass.simpleName}")
    println("in a list:   ${(listOf(a)[0] as Any).javaClass.simpleName}")
    println("a == Amount(1999): ${a == Amount(1_999)}")

    // Wrong move. Uncomment, predict the error, then run.
    // println(a === Amount(1_999))
}
