package workbench.patterns.l04;

/**
 * The pretend program that runs the shop's warehouse. It was bought years ago, and you can't change
 * it. Its shape is typical of old programs: weights as decimal strings in kilograms, products as the
 * warehouse's own item numbers, results packed into one string with a two-digit code, and a checked
 * exception for anything that goes wrong on the line. Given; don't edit.
 */
public class OldWarehouseSystem {

    /**
     * Puts some stock aside for an order.
     *
     * @param itemNumber the warehouse's item number, such as "4711"
     * @param kilos      the weight in kilograms as a plain decimal string, such as "1.250"
     * @return "code|holdId", for example "00|H4711" (held) or "51|" (out of stock)
     * @throws WarehouseException when the warehouse can't be reached
     */
    public String hold(String itemNumber, String kilos) throws WarehouseException {
        // the pretend warehouse holds anything up to 50 kg and answers 51 for more
        boolean small = new java.math.BigDecimal(kilos).compareTo(new java.math.BigDecimal("50")) <= 0;
        return small ? "00|H" + itemNumber : "51|";
    }
}
