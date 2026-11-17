package workbench.container.l01.demo

// The smallest container that works: read a constructor, build its parameters first, then call it.
class KSeatingPlan { init { println("  new KSeatingPlan") } }
class KPriceList(plan: KSeatingPlan) { init { println("  new KPriceList") } }
class KSeatFinder(plan: KSeatingPlan) { init { println("  new KSeatFinder") } }
class KBoxOffice(prices: KPriceList, finder: KSeatFinder) { init { println("  new KBoxOffice") } }

fun build(type: Class<*>): Any {
    val constructor = type.constructors[0]                           // 1. the recipe is the constructor
    val args = constructor.parameterTypes.map { build(it) }          // 2. build what it needs first
    return constructor.newInstance(*args.toTypedArray())             // 3. then the object itself
}

fun main() {
    println("by hand:")
    val plan = KSeatingPlan()
    KBoxOffice(KPriceList(plan), KSeatFinder(plan))

    println("by reflection:")
    build(KBoxOffice::class.java)
}
