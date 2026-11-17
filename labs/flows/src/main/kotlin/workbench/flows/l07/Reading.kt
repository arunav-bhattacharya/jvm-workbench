package workbench.flows.l07

/** One reading of an oven's thermometer, for example the main oven at 180 °C. Equality is the data class's. */
data class Reading(val oven: String, val celsius: Int)
