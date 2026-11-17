package workbench.functional.l01.demo

// Pure: the result depends only on the argument, and calling it changes nothing.
fun batterGrams(pancakes: Int): Int = pancakes * 55

// Impure: taking an egg out of the fridge is the whole point of the call. This fake fridge counts them.
object FakeFridge {
    var taken = 0
    fun takeEgg(): String {
        taken++
        return "egg_$taken"
    }
}

fun main() {
    // 1. With a pure function, a call and its value are interchangeable.
    val b = batterGrams(8)
    println("batterGrams(8) + batterGrams(8) = ${batterGrams(8) + batterGrams(8)}")
    println("val b = batterGrams(8); b + b   = ${b + b}")

    // 2. The same "harmless" refactoring on an impure call changes what the program does.
    val e = FakeFridge.takeEgg()
    println("val e = takeEgg(); listOf(e, e)  -> ${listOf(e, e)}, eggs taken: ${FakeFridge.taken}")

    FakeFridge.taken = 0
    val both = listOf(FakeFridge.takeEgg(), FakeFridge.takeEgg())
    println("listOf(takeEgg(), takeEgg())     -> $both, eggs taken: ${FakeFridge.taken}")
}
