package workbench.patterns.l02

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test

class FactoryTest {

    private fun valid(raw: String): Parcel {
        val r = Parcel.parse(raw)
        assertThat(r).`as`("parse(\"$raw\")").isInstanceOf(ParcelResult.Valid::class.java)
        return (r as ParcelResult.Valid).parcel
    }

    private fun reason(raw: String): String {
        val r = Parcel.parse(raw)
        assertThat(r).`as`("parse(\"$raw\")").isInstanceOf(ParcelResult.Invalid::class.java)
        return (r as ParcelResult.Invalid).reason
    }

    @Test
    fun `two and a half kilos parses to a bike parcel of 2500 grams`() {
        val parcel = valid("2.5 kg")
        assertThat(parcel.courier).isEqualTo(Courier.BIKE)
        assertThat(parcel.grams).isEqualTo(2_500)
    }

    @Test
    fun `grams and kilograms both work, and 5 kg is the most a bike takes`() {
        assertThat(valid("800 g").grams).isEqualTo(800)
        assertThat(valid(" 800 g ").courier).isEqualTo(Courier.BIKE)
        assertThat(valid("5 kg").courier).isEqualTo(Courier.BIKE)
        assertThat(valid("5.5 kg").courier).isEqualTo(Courier.VAN)
        assertThat(valid("30 kg").courier).isEqualTo(Courier.VAN)
        assertThat(valid("30 kg").grams).isEqualTo(30_000)
    }

    @Test
    fun `bad input comes back as Invalid with a reason, in the documented order`() {
        assertThat(reason("2.5kg")).isEqualTo("format")
        assertThat(reason("two kg")).isEqualTo("format")
        assertThat(reason("3 lb")).`as`("pounds are not a unit we take").isEqualTo("format")
        assertThat(reason("")).isEqualTo("format")
        assertThat(reason("0 g")).isEqualTo("weight")
        assertThat(reason("-1 kg")).isEqualTo("weight")
        assertThat(reason("31 kg")).isEqualTo("too heavy")
        assertThat(reason("30001 g")).isEqualTo("too heavy")
    }

    @Test
    fun `every courier has a family that reports its own courier`() {
        for (c in Courier.entries) {
            assertThat(CourierServices.forCourier(c).courier).isEqualTo(c)
        }
        assertThat(CourierServices.forCourier(Courier.BIKE).company).isEqualTo("Pedal Post")
        assertThat(CourierServices.forCourier(Courier.VAN).company).isEqualTo("Big Blue Vans")
    }

    @Test
    fun `a family's booker and tracker work together`() {
        val bike = CourierServices.forCourier(Courier.BIKE)
        val ref = bike.booker().book(valid("2.5 kg"), "o-17")
        assertThat(ref).isEqualTo("PP-o-17-2500")
        assertThat(bike.tracker().track(ref)).isEqualTo("Pedal Post: PP-o-17-2500 is on its way")

        val van = CourierServices.forCourier(Courier.VAN)
        val vanRef = van.booker().book(valid("12 kg"), "o-18")
        assertThat(vanRef).isEqualTo("BB-o-18-12000")
        assertThat(van.tracker().track(vanRef)).isEqualTo("Big Blue Vans: BB-o-18-12000 is on its way")
    }

    @Test
    fun `families refuse to mix couriers`() {
        val bike = CourierServices.forCourier(Courier.BIKE)
        val van = CourierServices.forCourier(Courier.VAN)
        assertThatThrownBy { bike.booker().book(valid("12 kg"), "o-1") }
            .isInstanceOf(IllegalArgumentException::class.java)
        assertThatThrownBy { van.tracker().track("PP-o-17-2500") }
            .isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `shipping books through the family the factory returns for the parcel's courier`() {
        val asked = mutableListOf<Courier>()
        val shipping = Shipping { courier -> asked += courier; CourierServices.forCourier(courier) }
        assertThat(shipping.ship("o-21", "12 kg")).isEqualTo(ShipResult.Booked("BB-o-21-12000"))
        assertThat(shipping.ship("o-22", "800 g")).isEqualTo(ShipResult.Booked("PP-o-22-800"))
        assertThat(asked).containsExactly(Courier.VAN, Courier.BIKE)
    }

    @Test
    fun `shipping rejects a bad weight without ever calling the factory`() {
        var calls = 0
        val shipping = Shipping { courier -> calls++; CourierServices.forCourier(courier) }
        assertThat(shipping.ship("o-23", "lots")).isEqualTo(ShipResult.Rejected("format"))
        assertThat(shipping.ship("o-24", "250 kg")).isEqualTo(ShipResult.Rejected("too heavy"))
        assertThat(calls).isZero()
    }

    @Test
    fun `shipping works with any factory, including a fake one`() {
        val fake = object : CourierServices {
            override val courier = Courier.BIKE
            override val company = "Test Courier"
            override fun booker() = Booker { parcel, orderId -> "FAKE-$orderId-${parcel.grams}" }
            override fun tracker() = Tracker { error("not used") }
        }
        assertThat(Shipping { fake }.ship("o-25", "7 g")).isEqualTo(ShipResult.Booked("FAKE-o-25-7"))
    }
}
