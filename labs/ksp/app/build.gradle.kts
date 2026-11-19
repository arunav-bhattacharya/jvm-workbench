// The KSP track's real-build playground: an ordinary project that applies the KSP Gradle plugin.
// One source set per lesson (src/lNN/kotlin), each processed only by that lesson's processor jar from :ksp
// (plus the lessons named in src/lNN/processors.txt). Set up by processorLab("ksp") in labs/build.gradle.kts;
// brief/outlines/ksp-labs.md explains it. Adding a lesson needs no edit here.
//   ./gradlew :ksp:app:kspL02Kotlin                 run lesson 2's reference processor, see build/generated/ksp/l02
//   ./gradlew :ksp:app:test -Pmine=l02              build and test with YOUR lesson 2 processor
