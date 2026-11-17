package workbench.bytecode.l03

// Lambdas, a function reference, a string template and a data class, compiled by kotlinc 2.4.21.

data class KCue(val name: String, val seconds: Int)

fun addSeconds(a: Int, b: Int) = a + b

fun greeter(): () -> String = { "hello" }                 // captures nothing
fun delay(extra: Int): (Int) -> Int = { s -> s + extra }  // captures extra

fun main() {
    val ref: (Int, Int) -> Int = ::addSeconds
    val c = ref.javaClass
    println("function ref: ${ref(90, 30)}, class ${c.name}")
    println("hidden: ${c.isHidden}")

    val lambda = greeter()
    println("lambda class ${lambda.javaClass.name}, hidden: ${lambda.javaClass.isHidden}")
    println("captures nothing: same object both times? ${greeter() === greeter()}")
    val d5 = delay(5)
    val d10 = delay(10)
    println("captures extra: same object? ${d5 === d10}, same class? ${d5.javaClass == d10.javaClass}")

    val cue = KCue("thunder", 90)
    println("template: ${cue.seconds} s to ${cue.name}, data class: $cue")
}
