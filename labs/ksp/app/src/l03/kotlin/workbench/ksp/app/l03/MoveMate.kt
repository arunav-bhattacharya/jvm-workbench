package workbench.ksp.app.l03

import workbench.ksp.annotations.Fragile
import workbench.ksp.annotations.Label
import workbench.ksp.annotations.Room
import workbench.ksp.annotations.l03.Care
import workbench.ksp.annotations.l03.Handling

// Lesson 3, the real build: the @Label processor reads these labels, and the Java class next door,
// labs/ksp/app/src/l03/java/workbench/ksp/app/l03/MovingCrate.java.
//   ./gradlew :ksp:app:kspL03Kotlin -Pmine=l03          run KSP alone with yours; it works even on the stub
//   then open labs/ksp/app/build/generated/ksp/l03/kotlin/workbench/ksp/app/l03/
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l03.MoveMateKt -Pmine=l03     once your lab passes

@Label
data class Lamp(val name: String, val bulbs: Int, val shade: String?)

@Label @Room("study") @Handling(care = Care.UPRIGHT, stackable = false, packWith = Lamp::class)
class Bookshelf(val shelves: Int, val books: List<String>)

@Label @Room("conservatory") @Handling(care = Care.GENTLE)
data class Plant(val kind: String, val potLitres: Double, val waterEveryDays: Int = 7)

@Label @Room("hall")
class Mirror(val widthCm: Int, val heightCm: Int, @Fragile val glass: String) {
    // the processor sees this function's name and return type, never the arithmetic inside it
    fun areaCm2(): Int = widthCm * heightCm
}

fun main() {
    println(LampLabel.SHAPE)
    println("${BookshelfLabel.SHAPE} -> ${BookshelfLabel.ROOM}, ${BookshelfLabel.HANDLING}")
    println("${PlantLabel.SHAPE} -> ${PlantLabel.ROOM}, ${PlantLabel.HANDLING}")
    println("${MirrorLabel.SHAPE} -> ${MirrorLabel.ROOM}")
    println(MovingCrateLabel.SHAPE)
}
