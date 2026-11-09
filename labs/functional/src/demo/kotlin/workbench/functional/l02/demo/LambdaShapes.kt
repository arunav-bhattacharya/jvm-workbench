package workbench.functional.l02.demo

fun addFee(cents: Long): Long = cents + 30

fun nonCapturing(): (Long) -> Long = { it + 30 }               // uses nothing from outside
fun capturing(feeCents: Long): (Long) -> Long = { it + feeCents } // captures feeCents
fun topLevelRef(): (Long) -> Long = ::addFee                   // a function reference

class Merchant(private val feeCents: Long) {
    fun withFee(cents: Long): Long = cents + feeCents
}

fun boundRef(m: Merchant): (Long) -> Long = m::withFee          // a reference bound to one object

fun main() {
    val m = Merchant(30)
    println("non-capturing lambda: same object every time?  ${nonCapturing() === nonCapturing()}")
    println("capturing lambda: same object every time?      ${capturing(30) === capturing(30)}")
    println("capturing lambdas equal with == ?              ${capturing(30) == capturing(30)}")
    println("unbound reference ::addFee: same object?       ${topLevelRef() === topLevelRef()}")
    println("bound reference m::withFee: same object?       ${boundRef(m) === boundRef(m)}")
    println()
    val lambda = nonCapturing().javaClass
    val ref = topLevelRef().javaClass
    println("lambda class:    ${lambda.name}  (hidden: ${lambda.isHidden})")
    println("reference class: ${ref.name}  (hidden: ${ref.isHidden}, extends ${ref.superclass.simpleName})")
}
