package workbench.ksp.app.l08

import workbench.ksp.annotations.Builder
import workbench.ksp.annotations.Inventory

@Inventory
@Builder
class Bookshelf(val shelves: Int, val books: List<String>)
