package workbench.container.l01.demo

// The smallest container that works: read a constructor, build its parameters first, then call it.
class KFxRates { init { println("  new KFxRates") } }
class KFeeCalculator(rates: KFxRates) { init { println("  new KFeeCalculator") } }
class KQuoteService(rates: KFxRates) { init { println("  new KQuoteService") } }
class KPaymentService(fees: KFeeCalculator, quotes: KQuoteService) { init { println("  new KPaymentService") } }

fun build(type: Class<*>): Any {
    val constructor = type.constructors[0]                           // 1. the recipe is the constructor
    val args = constructor.parameterTypes.map { build(it) }          // 2. build what it needs first
    return constructor.newInstance(*args.toTypedArray())             // 3. then the object itself
}

fun main() {
    println("by hand:")
    val rates = KFxRates()
    KPaymentService(KFeeCalculator(rates), KQuoteService(rates))

    println("by reflection:")
    build(KPaymentService::class.java)
}
