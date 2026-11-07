package workbench.bytecode.l03

// Lambdas, a function reference, a string template and a data class, compiled by kotlinc 2.4.21.

data class KFee(val currency: String, val amountMinor: Long)

fun addMinor(a: Int, b: Int) = a + b

fun greeter(): () -> String = { "hello" }                 // captures nothing
fun plus(fee: Int): (Int) -> Int = { x -> x + fee }       // captures fee

fun main() {
    val ref: (Int, Int) -> Int = ::addMinor
    val c = ref.javaClass
    println("function ref: ${ref(1_250, 30)}, class ${c.name}")
    println("hidden: ${c.isHidden}")

    val lambda = greeter()
    println("lambda class ${lambda.javaClass.name}, hidden: ${lambda.javaClass.isHidden}")
    println("captures nothing: same object both times? ${greeter() === greeter()}")
    val p30 = plus(30)
    val p45 = plus(45)
    println("captures fee: same object? ${p30 === p45}, same class? ${p30.javaClass == p45.javaClass}")

    val fee = KFee("EUR", 3_625)
    println("template: ${fee.amountMinor} ${fee.currency}, data class: $fee")
}
