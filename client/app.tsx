import {exposed} from 'newsroom-core';
import {STTCoverageVersionField} from './stt/STTCoverageVersionField';

exposed.agenda.registerCoverageFieldComponent('sttversion', STTCoverageVersionField);
