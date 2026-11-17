package workbench.kotlin.l02.demo

interface Counted {
    val count: Long
}

@JvmInline
value class Sheets(override val count: Long) : Counted

class PrintRun(val sheets: Sheets)                  // used as Sheets: stored as a long

fun <T> asGeneric(x: T): Any? = x                  // used as T: boxed
fun asNullable(s: Sheets?): Any? = s               // used as Sheets?: boxed
fun asInterface(c: Counted): Any = c               // used as Counted: boxed

fun main() {
    val s = Sheets(1_999)
    println("field in PrintRun: ${PrintRun::class.java.getDeclaredField("sheets").type}")
    println("as generic:        ${asGeneric(s)!!.javaClass.simpleName}")
    println("as nullable:       ${asNullable(s)!!.javaClass.simpleName}")
    println("as Counted:        ${asInterface(s).javaClass.simpleName}")
    println("in a list:         ${(listOf(s)[0] as Any).javaClass.simpleName}")
    println("s == Sheets(1999): ${s == Sheets(1_999)}")

    // Wrong move. Uncomment, predict the error, then run.
    // println(s === Sheets(1_999))
}
