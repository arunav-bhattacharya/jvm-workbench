package workbench.injector.app.l01

import workbench.injector.annotations.Inject
import workbench.injector.annotations.Singleton

/** The crew can't start until the truck and both packers are ready. */
@Singleton
class Crew @Inject constructor(val truck: Truck, val kitchenPacker: Packer, val bedroomPacker: Packer)
