package workbench.container.l01.demo

import workbench.container.l01.Container
import workbench.container.l01.ContainerException
import workbench.container.l01.Inject

// The same wiring with Kotlin classes, a cycle, and Kotlin's extra constructors.
class GSeatingPlan
class GPriceList(val plan: GSeatingPlan)
class GSalesBook
class GBoxOffice(val prices: GPriceList, val book: GSalesBook)

class GRota(val cast: GCastList)
class GCastList(val rehearsals: GRehearsalPlan)
class GRehearsalPlan(val rota: GRota)

class GPriceRules @Inject constructor(val feePercent: Int = 3)   // every parameter has a default

fun main() {
    val app = Container(listOf(GBoxOffice::class.java, GSalesBook::class.java, GPriceList::class.java, GSeatingPlan::class.java))
    println("creation order: " + app.creationOrder().map { it.simpleName })
    println("same PriceList: " + (app.get(GBoxOffice::class.java).prices === app.get(GPriceList::class.java)))

    for (components in listOf(listOf(GRota::class.java, GCastList::class.java, GRehearsalPlan::class.java),
                              listOf(GPriceRules::class.java))) {
        try {
            Container(components)
        } catch (e: ContainerException) {
            println("refused: ${e.message}")
        }
    }
}
