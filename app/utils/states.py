from aiogram.fsm.state import State, StatesGroup


class PostCreationState(StatesGroup):
    title = State()
    content = State()
    media = State()
    schedule_time = State()


class PostEditState(StatesGroup):
    edit_content = State()
    edit_media = State()
    edit_time = State()


class FreightCalculationState(StatesGroup):
    choosing_delivery_type = State()
    entering_origin_city = State()
    entering_destination_city = State()
    entering_weight = State()
    entering_volume = State()
    confirming_data = State()

    entering_origin_city_zhd = State()
    entering_destination_city_zhd = State()
    entering_weight_zhd = State()
    entering_volume_zhd = State()
    confirming_data_zhd = State()
    

class FreightContainerState(StatesGroup):
    entering_port = State()
    entering_city = State()
    entering_weight = State()
    entering_container_type = State()
    confirming_data = State()