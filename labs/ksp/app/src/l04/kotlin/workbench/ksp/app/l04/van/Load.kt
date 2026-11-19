package workbench.ksp.app.l04.van

import workbench.ksp.annotations.Builder
import workbench.ksp.app.l04.Box

// Lesson 4: a class in another package that uses Box, plus a nullable list of nullable boxes.
// LoadBuilder.kt needs `import workbench.ksp.app.l04.Box`, and KotlinPoet writes it.
@Builder
class Load(val first: Box, val spares: List<Box?>?)
