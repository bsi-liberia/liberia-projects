<template>
  <b-form-group :state="validation">
    <b-input type="number" step=".01"
    :name="totalValue"
    v-model="totalValue" size="30"
    :state="validation">
    </b-input>
  </b-form-group>
</template>
<script>
export default {
  data() {
    return { validation: null }
  },
  props: ["data"],
  computed: {
    totalValue: {
      get: function() {
        return ['Q1', 'Q2', 'Q3', 'Q4'].reduce((total, qtr) => {
          if (!(qtr in this.data.item)) { return total }
          return total + this.data.item[qtr].value
        }, 0.0)
      },
      set: function(newTotalValue) {
        var availableqtrs = ['Q1', 'Q2', 'Q3', 'Q4'].reduce((total, qtr) => {
          if (!(qtr in this.data.item)) { return total }
          total.push(qtr)
          return total
        }, [])
        availableqtrs.forEach(qtr => {
          this.data.item[qtr].value = (newTotalValue / availableqtrs.length)
        })
      }
    }
  }
}
</script>