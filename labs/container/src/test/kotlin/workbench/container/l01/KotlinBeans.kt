package workbench.container.l01

import workbench.container.l01.app.SeatingPlan

/** One parameter has a default: kotlinc adds a public synthetic constructor with a DefaultConstructorMarker. */
class KotlinPrices(val plan: SeatingPlan, val feePercent: Int = 3)

/** Every parameter has a default: kotlinc also adds a public no-argument constructor. */
class DefaultedPrices(val feePercent: Int = 3, val currency: String = "EUR")

/** The same shape, marked. kotlinc copies @Inject onto the no-argument constructor too. */
class InjectedPrices @Inject constructor(val feePercent: Int = 3, val currency: String = "EUR")
