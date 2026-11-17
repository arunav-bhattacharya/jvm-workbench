package workbench.functional.l02.demo

fun addRest(minutes: Long): Long = minutes + 10                   // let it rest 10 minutes

fun nonCapturing(): (Long) -> Long = { it + 10 }                  // uses nothing from outside
fun capturing(extra: Long): (Long) -> Long = { it + extra }       // captures extra
fun topLevelRef(): (Long) -> Long = ::addRest                     // a function reference

class Oven(private val extraMinutes: Long) {                      // this oven runs a little cold
    fun adjust(minutes: Long): Long = minutes + extraMinutes
}

fun boundRef(o: Oven): (Long) -> Long = o::adjust                 // a reference bound to one object

fun main() {
    val oven = Oven(5)
    println("non-capturing lambda: same object every time?  ${nonCapturing() === nonCapturing()}")
    println("capturing lambda: same object every time?      ${capturing(5) === capturing(5)}")
    println("capturing lambdas equal with == ?              ${capturing(5) == capturing(5)}")
    println("unbound reference ::addRest: same object?      ${topLevelRef() === topLevelRef()}")
    println("bound reference oven::adjust: same object?     ${boundRef(oven) === boundRef(oven)}")
    println()
    val lambda = nonCapturing().javaClass
    val ref = topLevelRef().javaClass
    println("lambda class:    ${lambda.name}  (hidden: ${lambda.isHidden})")
    println("reference class: ${ref.name}  (hidden: ${ref.isHidden}, extends ${ref.superclass.simpleName})")
}
