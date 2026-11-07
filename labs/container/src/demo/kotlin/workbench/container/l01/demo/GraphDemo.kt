package workbench.container.l01.demo

import workbench.container.l01.Container
import workbench.container.l01.ContainerException
import workbench.container.l01.Inject

// The same wiring with Kotlin classes, a cycle, and Kotlin's extra constructors.
class GFxRates
class GFeeCalculator(val rates: GFxRates)
class GLedger
class GPaymentService(val fees: GFeeCalculator, val ledger: GLedger)

class GPayouts(val statements: GStatements)
class GStatements(val reconciler: GReconciler)
class GReconciler(val payouts: GPayouts)

class GFeeRules @Inject constructor(val bps: Int = 290)        // every parameter has a default

fun main() {
    val app = Container(listOf(GPaymentService::class.java, GLedger::class.java, GFeeCalculator::class.java, GFxRates::class.java))
    println("creation order: " + app.creationOrder().map { it.simpleName })
    println("same FeeCalculator: " + (app.get(GPaymentService::class.java).fees === app.get(GFeeCalculator::class.java)))

    for (components in listOf(listOf(GPayouts::class.java, GStatements::class.java, GReconciler::class.java),
                              listOf(GFeeRules::class.java))) {
        try {
            Container(components)
        } catch (e: ContainerException) {
            println("refused: ${e.message}")
        }
    }
}
