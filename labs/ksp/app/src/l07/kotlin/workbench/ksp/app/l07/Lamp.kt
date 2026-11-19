package workbench.ksp.app.l07

import workbench.ksp.annotations.Inventory

@Inventory
data class Lamp(val name: String, val bulbs: Int, val shade: String?)
