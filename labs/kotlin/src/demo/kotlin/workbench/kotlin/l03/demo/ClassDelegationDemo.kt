package workbench.kotlin.l03.demo

interface Printer {
    fun print(document: String): String
}

class Laser(private val name: String) : Printer {
    override fun print(document: String): String = "$document printed on $name"
    override fun toString(): String = "Laser($name)"
}

/** `by printer` forwards to the object passed in at construction, stored in a hidden final field. */
class FrontDesk(var printer: Printer) : Printer by printer

/** Delegating a Set forwards Set's methods, but not equals, hashCode or toString. */
class Tags(private val inner: MutableSet<String> = HashSet()) : MutableSet<String> by inner

fun main() {
    val desk = FrontDesk(Laser("laser-1"))
    println(desk.print("flyer.pdf"))
    desk.printer = Laser("laser-2")                        // swap the printer...
    println("after swap, printer = ${desk.printer}: ${desk.print("flyer.pdf")}")

    val a = Tags().apply { add("rush"); add("colour") }
    val b = Tags().apply { add("rush"); add("colour") }
    println("a = $a")
    println("a == b: ${a == b}, a.size = ${a.size}, \"rush\" in a: ${"rush" in a}")
}
