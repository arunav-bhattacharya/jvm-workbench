package workbench.ksp.app.l08

import workbench.ksp.annotations.Builder
import workbench.ksp.annotations.Inventory

// Lesson 8 tests these processors in memory; here they run in a real build, on the same kind of class.
//   ./gradlew :ksp:app:kspL08Kotlin       then open build/generated/ksp/l08/kotlin/workbench/ksp/app/l08/
@Inventory
@Builder
data class Lamp(val name: String, val bulbs: Int, val shade: String?)
