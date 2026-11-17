package workbench.generics.l10.demo

// The shop's fruit, used by the demos of this lesson (the Java twins use these Kotlin types too)
interface Fruit { val name: String; val grams: Int }
data class Apple(override val name: String, override val grams: Int) : Fruit { override fun toString() = name }
data class Lemon(override val name: String, override val grams: Int) : Fruit { override fun toString() = name }

/** Declared out, like a glass display case. Then someone cut a slot in the glass for add(). It compiles. */
class DisplayCase<out T>(first: T) {
    private val items = mutableListOf(first)
    fun add(item: @UnsafeVariance T) { items.add(item) }
    fun last(): T = items.last()
}

fun main() {
    // 1. The standard library uses @UnsafeVariance safely: contains only compares, it never stores.
    val weights: List<Number> = listOf(180, 150)            // List<Int> seen as List<Number>
    println("contains(150): ${weights.contains(150)}, contains(2.5): ${weights.contains(2.5)}")

    // 2. And because contains takes an E, the compiler can catch a nonsense check.
    // println(listOf(180, 150).contains("180"))             // wrong move 1

    // 3. Used carelessly, the same annotation breaks type safety.
    val apples: DisplayCase<Apple> = DisplayCase(Apple("Gala", 180))
    val anyFruit: DisplayCase<Fruit> = apples               // fine: DisplayCase is out T
    anyFruit.add(Lemon("Eureka", 120))                      // compiles, thanks to @UnsafeVariance
    try {
        val last: Apple = apples.last()
        println(last)
    } catch (e: ClassCastException) {
        println("ClassCastException: ${e.message?.substringBefore(" (")}")
    }
}

// Wrong move 2: remove @UnsafeVariance from a copy of DisplayCase and read the error.
// class DisplayCase2<out T> { fun add(item: T) {} }
