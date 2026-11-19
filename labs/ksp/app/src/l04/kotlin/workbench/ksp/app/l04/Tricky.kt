package workbench.ksp.app.l04

import workbench.ksp.annotations.Builder

// Lesson 4: the shapes that broke the string template. KotlinPoet handles each one.

class Kitchen {
    // a nested class: its builder is KitchenDrawerBuilder, and build() returns Kitchen.Drawer
    @Builder
    data class Drawer(val label: String, val handles: Int)
}

// property names that are Kotlin keywords: the builder writes them as `in` and `object`
@Builder
class Crate(val `in`: String, val `object`: String)
