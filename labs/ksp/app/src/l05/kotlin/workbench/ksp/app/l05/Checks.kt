package workbench.ksp.app.l05

// Lesson 5, Try it in the real build: add a bad class here, run `./gradlew :ksp:app:kspL05Kotlin`, read the
// message, then delete it again. For example:
//
//   @Builder
//   interface Wardrobe
//
// Every problem shows in one build, each with its file and line. Warnings don't stop the build.
//   ./gradlew :ksp:app:demo -Pmain=workbench.ksp.app.l05.ChecksKt

fun main() {
    val fern = PlantBuilder().kind("fern").potLitres(2.5).waterEveryDays(3).build()
    val plates = BoxBuilder().label("plates").room("kitchen").weightGrams(4200).fragile(true).build()
    println(fern)
    println(plates)
}
