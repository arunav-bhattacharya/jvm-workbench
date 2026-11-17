package workbench.flows.l04

// Shared model. This file is the same in src/main and src/solution.

/** One reading of the oven thermometer. [tick] counts from 1. */
data class Reading(val oven: String, val tick: Int, val celsius: Int)

/** What the little screen on the oven door shows for one reading. */
data class Shown(val tick: Int, val text: String)

/** One plate on its way from the cook to the table. */
data class Plate(val seq: Int, val dish: String)
