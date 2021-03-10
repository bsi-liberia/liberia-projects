<template>
  <b-form-group :state="validation">
    <b-input-group>
      <b-input-group-prepend is-text>
        <b-link title="Adjust currency and conversion rate" href="#"
          variant="outline-secondary" @click="currencyDetailPopup(transaction)">
        {{ currency }}
        </b-link>
      </b-input-group-prepend>
      <b-input :type="type" step=".01"
        :state="validation"
        :name="name" :placeholder="placeholder"
        v-model="_value" size="30" :disabled="disabled"
        v-on:change="update">
      </b-input>
      <b-input-group-append is-text>
        <b-link variant="outline-secondary" title="Adjust currency and conversion rate" href="#"
           @click="currencyDetailPopup(transaction)">
          <font-awesome-icon :icon="['fa', 'cog']" />
        </b-link>
      </b-input-group-append>
    </b-input-group>
  </b-form-group>
</template>
<script>
export default {
  data() {
    return { validation: null }
  },
  props: ["transaction", "type", "name", "placeholder", "value", "disabled", "currency"],
  inject: ['updateFinances', 'currencyDetailPopup'],
  methods: {
    update(newValue, oldValue) {
      this.updateFinances(this, this.transaction, this.name, newValue, oldValue)
      this.validation = true
      this.$emit('update:value', newValue)
    },
  },
  computed: {
    _value: {
     // getter
      get: function () {
        return this.value
      },
      // setter
      set: function (newValue) {
        return
      }
    }
  }
}
</script>