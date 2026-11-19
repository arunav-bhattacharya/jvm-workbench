package workbench.ksp.app.l07

import workbench.ksp.annotations.Inventory

// One box per file, so the incremental log can show which files KSP reads again.
@Inventory
data class Box(val label: String, val room: String, val weightGrams: Int, val fragile: Boolean = false)
