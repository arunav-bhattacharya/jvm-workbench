package workbench.container.l01

import workbench.container.l01.app.FxRates

/** One parameter has a default: kotlinc adds a public synthetic constructor with a DefaultConstructorMarker. */
class KotlinFees(val rates: FxRates, val bps: Int = 290)

/** Every parameter has a default: kotlinc also adds a public no-argument constructor. */
class DefaultedFees(val bps: Int = 290, val currency: String = "EUR")

/** The same shape, marked. kotlinc copies @Inject onto the no-argument constructor too. */
class InjectedFees @Inject constructor(val bps: Int = 290, val currency: String = "EUR")
