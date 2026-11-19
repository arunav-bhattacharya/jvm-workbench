// The injector capstone's real-build playground: an ordinary project that applies the KSP Gradle plugin.
// One source set per lesson (src/lNN/kotlin), each processed only by that lesson's processor jar from :injector
// (plus the lessons named in src/lNN/processors.txt). Set up by processorLab("injector") in labs/build.gradle.kts;
// brief/outlines/ksp-labs.md explains it. Adding a lesson needs no edit here.
//   ./gradlew :injector:app:kspL01Kotlin            run lesson 1's reference processor, see build/generated/ksp/l01
//   ./gradlew :injector:app:test -Pmine=l01         build and test with YOUR lesson 1 processor
