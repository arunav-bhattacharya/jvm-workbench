package workbench.generics.l06.demo

/** Weighs any mutable crate of fruit. It only takes fruit out, so it asks for an out-projection. */
fun totalGrams(crate: MutableList<out Fruit>): Int {
    var sum = 0
    for (f in crate) sum += f.grams              // reads come out as Fruit
    // crate.add(Apple("Gala", 180))             // wrong move 1: no add() through an out-projection
    return sum
}

fun main() {
    val apples: MutableList<Apple> = mutableListOf(Apple("Gala", 180), Apple("Fuji", 150))
    val lemons: MutableList<Lemon> = mutableListOf(Lemon("Eureka", 120))
    println("apples: ${totalGrams(apples)} g, lemons: ${totalGrams(lemons)} g")

    val view: MutableList<out Fruit> = apples   // the same projection on a variable
    view.removeAt(0)                            // still allowed: removeAt takes an Int, not a T
    println("after removeAt through the view: $apples")

    // Wrong move 2: no projection, so a MutableList<Apple> is not a MutableList<Fruit>.
    // val strict: MutableList<Fruit> = apples
}
