package workbench.generics.l06.demo

/** Takes T in AND hands T out, so it can't be declared out or in. It stays invariant. */
class Crate<T> {
    private val items = mutableListOf<T>()
    fun put(item: T) { items += item }
    fun top(): T = items.last()
}

// Only takes out: ask for a take-only view. A Crate<Apple> fits.
fun topName(crate: Crate<out Fruit>): String = crate.top().name

// Only puts apples in: ask for a drop-only view. A Crate<Fruit> fits.
fun putApple(crate: Crate<in Apple>, name: String, grams: Int) = crate.put(Apple(name, grams))

fun main() {
    val apples = Crate<Apple>()
    val mixed = Crate<Fruit>()
    mixed.put(Lemon("Eureka", 120))

    putApple(apples, "Gala", 180)
    putApple(mixed, "Fuji", 150)
    println("${topName(apples)} ${topName(mixed)}")

    // Wrong move: the class is invariant, so the plain type still doesn't fit.
    // val strict: Crate<Fruit> = apples
}

// Predict each line, then uncomment it alone and run.
// fun redundant(fruit: List<out Fruit>) {}          // 1
// fun conflicting(fruit: List<in Fruit>) {}         // 2
// fun <out T> onFunction(t: T) {}                   // 3
