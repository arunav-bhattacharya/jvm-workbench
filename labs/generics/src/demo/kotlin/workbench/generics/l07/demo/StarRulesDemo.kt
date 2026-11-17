package workbench.generics.l07.demo

// The shop's fruit, used by the demos of this lesson (the Java twins use these Kotlin types too)
interface Fruit { val name: String; val grams: Int }
data class Apple(override val name: String, override val grams: Int) : Fruit {
    override fun toString() = name                 // prints as "Gala", not "Apple(name=Gala, grams=180)"
}
data class Lemon(override val name: String, override val grams: Int) : Fruit {
    override fun toString() = name
}

/** From lesson 4, with a "fruit only" bound: out T. Dispenser<*> means Dispenser<out Fruit>. */
interface Dispenser<out T : Fruit> { fun next(): T }

/** From lesson 5: in T. Bin<*> means Bin<in Nothing>. */
interface Bin<in T> { fun drop(item: T) }

/** From lesson 1: invariant T. Box<*> reads as Box<out Any?> and writes as Box<in Nothing>. */
class Box<T>(var item: T)

fun peek(dispenser: Dispenser<*>): Fruit = dispenser.next()   // the "fruit only" sign survives the star
fun peek(box: Box<*>): Any? = box.item

fun main() {
    val apples: Dispenser<Apple> = object : Dispenser<Apple> { override fun next() = Apple("Gala", 180) }
    val compost: Bin<Fruit> = object : Bin<Fruit> { override fun drop(item: Fruit) = println("compost: $item") }
    val box: Box<Int> = Box(180)

    println("peek(dispenser) = ${peek(apples)}, peek(box) = ${peek(box)}")

    compost.drop(Lemon("Eureka", 95))           // through the real type: fine
    val someBin: Bin<*> = compost               // through *: nothing can be dropped in
    val someBox: Box<*> = box
    println("a Box<*> still reads: ${someBox.item}")

    // Wrong moves. Uncomment one at a time, predict the error, then run.
    // someBin.drop(Apple("Fuji", 150))         // 1
    // someBox.item = 150                       // 2
    // val a: Apple = peek(apples)              // 3
}
