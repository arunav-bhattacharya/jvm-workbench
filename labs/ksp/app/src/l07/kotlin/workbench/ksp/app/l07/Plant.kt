package workbench.ksp.app.l07

import workbench.ksp.annotations.Inventory

@Inventory
data class Plant(val kind: String, val potLitres: Double, val waterEveryDays: Int = 7)
